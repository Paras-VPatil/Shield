from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, BackgroundTasks
from fastapi.responses import PlainTextResponse

from app.core.security import get_current_user
from app.models.request_models import MeetingAnalyzeRequest, MeetingCreateRequest
from app.models.response_models import (
    MeetingAnalyzeResponse,
    MeetingDetailResponse,
    MeetingSummary,
    RevisionResponse,
    BulkJobStatus,
)
from app.services.llm_service import LLMService
from app.services.meeting_service import (
    add_minutes_pdf,
    analyze_meeting_content,
    create_meeting,
    export_meeting_transcript,
    get_meeting,
    get_meeting_revisions,
    list_meetings,
    start_bulk_analysis,
    get_job_status,
    process_bulk_job,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])
llm_service = LLMService()


@router.get("", response_model=list[MeetingSummary])
async def get_meetings(user: dict = Depends(get_current_user)) -> list[MeetingSummary]:
    meetings = list_meetings(user["id"])
    return [MeetingSummary(**meeting) for meeting in meetings]


@router.post("", response_model=MeetingSummary)
async def create_meeting_endpoint(
    payload: MeetingCreateRequest,
    user: dict = Depends(get_current_user),
) -> MeetingSummary:
    meeting = create_meeting(user["id"], payload.title)
    return MeetingSummary(
        id=meeting["id"],
        title=meeting["title"],
        created_at=meeting["created_at"],
        updated_at=meeting["updated_at"],
    )


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
async def get_meeting_endpoint(
    meeting_id: str,
    user: dict = Depends(get_current_user),
) -> MeetingDetailResponse:
    meeting = get_meeting(user["id"], meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found.")
    return MeetingDetailResponse(
        id=meeting["id"],
        title=meeting["title"],
        created_at=meeting["created_at"],
        updated_at=meeting["updated_at"],
        domains=meeting.get("domains", []),
        open_questions=meeting.get("open_questions", []),
        resolved_questions=meeting.get("resolved_questions", []),
        minutes=meeting.get("minutes", []),
        analysis_history=meeting.get("analysis_history", []),
    )


@router.post("/{meeting_id}/minutes/pdf")
async def upload_meeting_minutes_pdf(
    meeting_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> dict:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported.")
    content = await file.read()
    try:
        entry = add_minutes_pdf(user["id"], meeting_id, file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"message": "PDF uploaded.", "entry_id": entry["id"], "chars": len(entry["text"])}


@router.post("/{meeting_id}/analyze", response_model=MeetingAnalyzeResponse)
async def analyze_meeting_endpoint(
    meeting_id: str,
    payload: MeetingAnalyzeRequest,
    user: dict = Depends(get_current_user),
) -> MeetingAnalyzeResponse:
    try:
        analysis = analyze_meeting_content(
            user_id=user["id"],
            meeting_id=meeting_id,
            text=payload.text or "",
            speaker_segments=[segment.model_dump() for segment in payload.speaker_segments],
            llm_service=llm_service,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MeetingAnalyzeResponse(**analysis)


@router.post("/{meeting_id}/bulk", response_model=BulkJobStatus)
async def analyze_bulk_endpoint(
    meeting_id: str,
    payload: dict, # Expecting {"requirements": [...]}
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
) -> BulkJobStatus:
    requirements = payload.get("requirements", [])
    if not requirements:
        raise HTTPException(status_code=400, detail="No requirements provided.")
    
    job = start_bulk_analysis(user["id"], meeting_id, requirements)
    background_tasks.add_task(
        process_bulk_job,
        job["job_id"],
        user["id"],
        meeting_id,
        requirements,
        llm_service
    )
    return BulkJobStatus(**job)


@router.get("/jobs/{job_id}", response_model=BulkJobStatus)
async def get_job_status_endpoint(
    job_id: str,
    user: dict = Depends(get_current_user),
) -> BulkJobStatus:
    job = get_job_status(user["id"], job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return BulkJobStatus(**job)


@router.get("/{meeting_id}/transcript")
async def download_meeting_transcript(
    meeting_id: str,
    user: dict = Depends(get_current_user),
) -> PlainTextResponse:
    try:
        transcript = export_meeting_transcript(user["id"], meeting_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    response = PlainTextResponse(content=transcript)
    response.headers["Content-Disposition"] = f'attachment; filename="meeting-{meeting_id}.txt"'
    return response


@router.get("/{meeting_id}/revisions", response_model=RevisionResponse)
async def get_meeting_revisions_endpoint(
    meeting_id: str,
    user: dict = Depends(get_current_user),
) -> RevisionResponse:
    try:
        revisions = get_meeting_revisions(user["id"], meeting_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RevisionResponse(**revisions)
