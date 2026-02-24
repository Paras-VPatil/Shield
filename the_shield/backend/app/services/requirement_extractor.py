import re

from app.utils.text_cleaner import normalize_text

BULLET_PREFIX_PATTERN = re.compile(r"^\s*(?:[-*•]|\d+[\).\-\:])\s+")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[\.\!\?])\s+")


def _strip_bullet_prefix(text: str) -> str:
    return BULLET_PREFIX_PATTERN.sub("", text).strip()


def _cleanup_requirement(text: str) -> str:
    cleaned = normalize_text(_strip_bullet_prefix(text))
    return cleaned.strip(" -\t")


def extract_requirements(raw_text: str) -> list[str]:
    if not raw_text or not raw_text.strip():
        return []

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    candidates: list[str] = []

    if len(lines) > 1:
        for line in lines:
            item = _cleanup_requirement(line)
            if item:
                candidates.append(item)
    else:
        paragraph = normalize_text(raw_text)
        sentences = [segment.strip() for segment in SENTENCE_SPLIT_PATTERN.split(paragraph) if segment.strip()]
        if len(sentences) > 1:
            candidates.extend(_cleanup_requirement(sentence) for sentence in sentences)
        else:
            candidates.append(_cleanup_requirement(paragraph))

    results: list[str] = []
    seen = set()
    for item in candidates:
        if len(item) < 3:
            continue
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        results.append(item)

    return results
