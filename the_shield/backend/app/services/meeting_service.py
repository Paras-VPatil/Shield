import io
import re
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pypdf import PdfReader

from app.database.db import load_db, save_db
from app.services.analysis_engine import run_requirement_analysis
from app.services.llm_service import LLMService
from app.utils.helpers import unique_in_order

STOP_WORDS = {
    "what",
    "which",
    "how",
    "should",
    "would",
    "could",
    "will",
    "must",
    "is",
    "are",
    "the",
    "for",
    "and",
    "this",
    "that",
    "with",
    "from",
    "into",
    "to",
    "of",
    "in",
    "be",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_meetings(user_id: str) -> list[dict]:
    data = load_db()
    return [
        {
            "id": meeting["id"],
            "title": meeting["title"],
            "created_at": meeting["created_at"],
            "updated_at": meeting["updated_at"],
        }
        for meeting in data["meetings"]
        if meeting["owner_id"] == user_id
    ]


def create_meeting(user_id: str, title: str) -> dict:
    data = load_db()
    meeting = {
        "id": str(uuid4()),
        "title": title.strip(),
        "owner_id": user_id,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "domains": [],
        "minutes": [],
        "analysis_history": [],
        "open_questions": [],
        "resolved_questions": [],
        "speaker_notes": [],
    }
    data["meetings"].append(meeting)
    save_db(data)
    return meeting


def get_meeting(user_id: str, meeting_id: str) -> Optional[dict]:
    data = load_db()
    return next(
        (meeting for meeting in data["meetings"] if meeting["id"] == meeting_id and meeting["owner_id"] == user_id),
        None,
    )


def _extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        pages.append((page.extract_text() or "").strip())
    return "\n".join(page for page in pages if page)


def add_minutes_pdf(user_id: str, meeting_id: str, filename: str, file_bytes: bytes) -> dict:
    data = load_db()
    meeting = next(
        (meeting for meeting in data["meetings"] if meeting["id"] == meeting_id and meeting["owner_id"] == user_id),
        None,
    )
    if meeting is None:
        raise ValueError("Meeting not found.")

    text = _extract_pdf_text(file_bytes).strip()
    entry = {
        "id": str(uuid4()),
        "source": "pdf",
        "filename": filename,
        "text": text,
        "created_at": _now_iso(),
    }
    meeting["minutes"].append(entry)
    meeting["updated_at"] = _now_iso()
    save_db(data)
    return entry


def _question_keywords(question: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9\-]+", question.lower())
    return {token for token in tokens if len(token) > 3 and token not in STOP_WORDS}


def _resolved_by_patterns(question: str, text: str) -> bool:
    q = question.lower()
    t = text.lower()
    pattern_checks = [
        (["oauth", "provider"], ["google", "microsoft", "github", "apple", "okta"]),
        (["privacy", "standard"], ["hipaa", "gdpr", "fhir", "hl7"]),
        (["doctor", "modify", "record"], ["read-only", "readonly", "can edit", "cannot edit", "update"]),
        (["permission", "role"], ["rbac", "role based", "admin", "doctor", "user"]),
        (["ai", "analytics"], ["risk", "insight", "prediction", "dashboard", "report"]),
    ]
    for question_markers, answer_markers in pattern_checks:
        if all(marker in q for marker in question_markers) and any(marker in t for marker in answer_markers):
            return True
    return False


def _match_resolved_questions(open_questions: list[str], clarification_text: str) -> tuple[list[str], list[str]]:
    lower = clarification_text.lower()
    resolved: list[str] = []
    still_open: list[str] = []
    decision_cues = ["will ", "must ", "should ", "use ", "supports ", "follow ", "chosen ", "decided "]
    has_decision = any(cue in lower for cue in decision_cues)

    for question in open_questions:
        keywords = _question_keywords(question)
        if not keywords:
            still_open.append(question)
            continue
        hits = sum(1 for keyword in keywords if keyword in lower)
        dynamic_threshold = 1 if len(keywords) <= 3 else 2
        if (has_decision and hits >= dynamic_threshold) or _resolved_by_patterns(question, lower):
            resolved.append(question)
        else:
            still_open.append(question)
    return resolved, still_open


def _compose_text(text: str, speaker_segments: list[dict]) -> str:
    parts: list[str] = []
    if text.strip():
        parts.append(text.strip())
    for segment in speaker_segments:
        speaker = segment["speaker"].strip()
        segment_text = segment["text"].strip()
        if segment_text:
            parts.append(f"{speaker}: {segment_text}")
    return "\n".join(parts).strip()


def _collect_previous_context(meeting: dict, max_chars: int = 4500) -> str:
    parts: list[str] = []

    open_questions = meeting.get("open_questions", [])
    if open_questions:
        parts.append("Previously open questions:")
        for question in open_questions[:10]:
            parts.append(f"- {question}")

    minutes = meeting.get("minutes", [])
    if minutes:
        parts.append("Previous meeting minutes context:")
        for entry in minutes[-3:]:
            text = (entry.get("text") or "").strip()
            if not text:
                continue
            source = entry.get("source", "unknown")
            parts.append(f"[{source}] {text}")

    speaker_notes = meeting.get("speaker_notes", [])
    if speaker_notes:
        parts.append("Previous speaker notes context:")
        for note in speaker_notes[-12:]:
            speaker = note.get("speaker", "Speaker")
            text = (note.get("text") or "").strip()
            if text:
                parts.append(f"{speaker}: {text}")

    joined = "\n".join(parts).strip()
    if len(joined) <= max_chars:
        return joined
    return joined[-max_chars:]


def analyze_meeting_content(
    user_id: str,
    meeting_id: str,
    text: str,
    speaker_segments: list[dict],
    llm_service: LLMService,
) -> dict:
    data = load_db()
    meeting = next(
        (meeting for meeting in data["meetings"] if meeting["id"] == meeting_id and meeting["owner_id"] == user_id),
        None,
    )
    if meeting is None:
        raise ValueError("Meeting not found.")

    combined_text = _compose_text(text, speaker_segments)
    if not combined_text:
        raise ValueError("No meeting content provided.")

    previous_context = _collect_previous_context(meeting)
    analysis = run_requirement_analysis(
        combined_text,
        llm_service,
        context_text=previous_context,
    )
    resolved_now, still_open = _match_resolved_questions(meeting["open_questions"], combined_text)

    new_open_questions = [question for question in analysis["questions"] if question not in resolved_now]
    meeting["open_questions"] = unique_in_order(still_open + new_open_questions)
    meeting["resolved_questions"] = unique_in_order(meeting["resolved_questions"] + resolved_now)
    meeting["domains"] = unique_in_order(meeting["domains"] + analysis["domains"])

    if text.strip():
        meeting["minutes"].append(
            {
                "id": str(uuid4()),
                "source": "text",
                "text": text.strip(),
                "created_at": _now_iso(),
            }
        )

    for segment in speaker_segments:
        meeting["speaker_notes"].append(
            {
                "id": str(uuid4()),
                "speaker": segment["speaker"].strip(),
                "text": segment["text"].strip(),
                "created_at": _now_iso(),
            }
        )

    history_entry = {
        "id": str(uuid4()),
        "created_at": _now_iso(),
        "input_text": combined_text,
        "analysis": {
            "status": analysis["status"],
            "message": analysis["message"],
            "domains": analysis["domains"],
            "questions": analysis["questions"],
            "resolved_now": resolved_now,
            "open_after_analysis": meeting["open_questions"],
            "sprint_plan": analysis.get("capability_insights", {}).get("sprint_plan", []),
            "proprietary_tool_suggestions": analysis.get("capability_insights", {}).get("proprietary_tool_suggestions", []),
        },
    }
    meeting["analysis_history"].append(history_entry)
    meeting["updated_at"] = _now_iso()
    save_db(data)

    return {
        **analysis,
        "meeting_id": meeting["id"],
        "open_questions": meeting["open_questions"],
        "resolved_questions": meeting["resolved_questions"],
    }


def export_meeting_transcript(user_id: str, meeting_id: str) -> str:
    meeting = get_meeting(user_id, meeting_id)
    if meeting is None:
        raise ValueError("Meeting not found.")

    lines: list[str] = []
    lines.append(f"Meeting: {meeting['title']}")
    lines.append(f"Meeting ID: {meeting['id']}")
    lines.append(f"Created: {meeting['created_at']}")
    lines.append(f"Updated: {meeting['updated_at']}")
    lines.append("")

    domains = meeting.get("domains", [])
    lines.append(f"Detected Domains: {', '.join(domains) if domains else 'None'}")
    lines.append("")

    lines.append("Open Questions:")
    open_questions = meeting.get("open_questions", [])
    if open_questions:
        for idx, question in enumerate(open_questions, start=1):
            lines.append(f"{idx}. {question}")
    else:
        lines.append("None")
    lines.append("")

    lines.append("Resolved Questions:")
    resolved_questions = meeting.get("resolved_questions", [])
    if resolved_questions:
        for idx, question in enumerate(resolved_questions, start=1):
            lines.append(f"{idx}. {question}")
    else:
        lines.append("None")
    lines.append("")

    lines.append("Minutes Entries:")
    minutes = meeting.get("minutes", [])
    if minutes:
        for entry in minutes:
            source = entry.get("source", "unknown")
            created_at = entry.get("created_at", "")
            filename = entry.get("filename")
            heading = f"- [{created_at}] {source}"
            if filename:
                heading += f" ({filename})"
            lines.append(heading)
            text = entry.get("text", "").strip()
            if text:
                lines.append(text)
            lines.append("")
    else:
        lines.append("None")
        lines.append("")

    lines.append("Speaker Notes:")
    speaker_notes = meeting.get("speaker_notes", [])
    if speaker_notes:
        for note in speaker_notes:
            lines.append(
                f"- [{note.get('created_at', '')}] {note.get('speaker', 'Speaker')}: {note.get('text', '')}"
            )
    else:
        lines.append("None")
    lines.append("")

    lines.append("Analysis History:")
    history = meeting.get("analysis_history", [])
    if history:
        for item in history:
            created_at = item.get("created_at", "")
            status = item.get("analysis", {}).get("status", "unknown")
            message = item.get("analysis", {}).get("message", "")
            lines.append(f"- [{created_at}] status={status} | {message}")
    else:
        lines.append("None")
    lines.append("")

    return "\n".join(lines)


def get_meeting_revisions(user_id: str, meeting_id: str) -> dict:
    data = load_db()
    meeting = next(
        (meeting for meeting in data["meetings"] if meeting["id"] == meeting_id and meeting["owner_id"] == user_id),
        None,
    )
    if meeting is None:
        raise ValueError("Meeting not found.")

    history = meeting.get("analysis_history", [])
    if len(history) < 1:
        raise ValueError("No analysis history yet.")

    current = history[-1]
    previous = history[-2] if len(history) > 1 else None

    # For now, let's extract requirements from the input text as a proxy for diff
    # In a real app, we'd use the stored 'extracted_requirements' if we saved them in the snapshot
    # Since we didn't save them in the snapshot yet, let's just Compare the analysis status and questions
    
    curr_snap = current["analysis"]
    prev_snap = previous["analysis"] if previous else {}

    added_questions = [q for q in curr_snap.get("questions", []) if q not in prev_snap.get("questions", [])]
    removed_questions = [q for q in prev_snap.get("questions", []) if q not in curr_snap.get("questions", [])]

    return {
        "meeting_id": meeting_id,
        "previous_id": previous["id"] if previous else None,
        "current_id": current["id"],
        "added_requirements": [], # Placeholder as we don't store them in snapshot yet
        "removed_requirements": [],
        "added_questions": added_questions,
        "removed_questions": removed_questions,
        "status_changed": prev_snap.get("status") != curr_snap.get("status") if previous else False,
        "old_status": prev_snap.get("status"),
        "new_status": curr_snap.get("status"),
    }
