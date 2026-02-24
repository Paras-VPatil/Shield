from typing import Iterable, List


def unique_in_order(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def build_status_message(status: str, missing_fields: list[str], domain_gaps: list[str]) -> str:
    if status == "complete":
        return "Requirement appears complete for current heuristic checks."
    if status == "incomplete":
        missing = ", ".join(missing_fields)
        return f"Requirement is missing core components: {missing}."
    gap_count = len(domain_gaps)
    return f"Requirement has domain gaps that need clarification ({gap_count} detected)."
