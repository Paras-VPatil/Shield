import re


def normalize_text(text: str) -> str:
    stripped = text.strip()
    collapsed = re.sub(r"\s+", " ", stripped)
    return collapsed
