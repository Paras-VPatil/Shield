import re
from typing import Optional

from app.utils.text_cleaner import normalize_text

COMMON_ACTORS = [
    "user",
    "admin",
    "customer",
    "system",
    "manager",
    "guest",
    "operator",
    "staff",
]

ACTION_PATTERN = re.compile(
    r"\b("
    r"log in|login|logs in|logs into|sign in|signs in|"
    r"authenticate|authenticates|create|creates|update|updates|"
    r"delete|deletes|view|views|book|books|pay|pays|"
    r"submit|submits|generate|generates|process|processes|"
    r"store|stores|send|sends|receive|receives"
    r")\b",
    re.IGNORECASE,
)
MODAL_ACTION_PATTERN = re.compile(
    r"\b(?:shall|must|can|should|will|may)\s+([a-z]+)\b",
    re.IGNORECASE,
)
CONDITION_PATTERN = re.compile(
    r"\b(if|when|unless|after|before|while|once|until)\b(.+)$",
    re.IGNORECASE,
)


def _extract_actor(text: str) -> Optional[str]:
    if re.match(r"^(shall|must|can|should|will|may)\b", text, re.IGNORECASE):
        return None

    head_match = re.search(
        r"^(?:the\s+)?([A-Za-z][\w-]*(?:\s+[A-Za-z][\w-]*){0,2})\s+"
        r"(?:shall|must|can|should|will|may|is|are|has|have|had|"
        r"logs?|creates?|updates?|deletes?|views?|books?|pays?|"
        r"submits?|generates?|processes?|stores?|sends?|receives?)\b",
        text,
        re.IGNORECASE,
    )
    if head_match:
        return head_match.group(1).strip().lower()

    lower = text.lower()
    action_match = ACTION_PATTERN.search(text)
    action_index = action_match.start() if action_match else len(text)
    for actor in COMMON_ACTORS:
        actor_match = re.search(rf"\b{re.escape(actor)}\b", lower)
        if actor_match and actor_match.start() < action_index:
            return actor
    return None


def _extract_action(text: str) -> Optional[str]:
    modal_match = MODAL_ACTION_PATTERN.search(text)
    if modal_match:
        return modal_match.group(1).strip().lower()

    action_match = ACTION_PATTERN.search(text)
    if action_match:
        return action_match.group(1).strip().lower()
    return None


def _extract_conditions(text: str) -> Optional[str]:
    condition_match = CONDITION_PATTERN.search(text)
    if not condition_match:
        return None
    condition_text = f"{condition_match.group(1)}{condition_match.group(2)}"
    return condition_text.strip().rstrip(".")


def _strip_conditions_tail(text: str) -> str:
    split_match = re.split(
        r"\bif\b|\bwhen\b|\bunless\b|\bafter\b|\bbefore\b|\bwhile\b|\bonce\b|\buntil\b",
        text,
        flags=re.IGNORECASE,
    )
    return split_match[0].strip()


def _extract_object(text: str, action: Optional[str]) -> Optional[str]:
    if not action:
        return None

    action_search = re.search(rf"\b{re.escape(action)}\b", text, re.IGNORECASE)
    if not action_search:
        return None

    tail = text[action_search.end() :].strip()
    tail = _strip_conditions_tail(tail)
    tail = tail.strip(" .,:;")
    tail = re.sub(r"^(to|into|in|on)\s+", "", tail, flags=re.IGNORECASE)
    if not tail:
        return None
    return tail


def parse_requirement(text: str) -> dict[str, Optional[str]]:
    cleaned = normalize_text(text)
    actor = _extract_actor(cleaned)
    action = _extract_action(cleaned)
    obj = _extract_object(cleaned, action)
    conditions = _extract_conditions(cleaned)

    return {
        "actor": actor,
        "action": action,
        "obj": obj,
        "conditions": conditions,
    }
