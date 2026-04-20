from typing import Iterable, List, Any


def unique_in_order(items: Iterable[Any]) -> List[Any]:
    seen = set()
    result: List[Any] = []
    for item in items:
        key = item
        if isinstance(item, dict):
            # Dicts are not hashable, use a stable tuple representation
            key = tuple(sorted(item.items()))
        
        if key not in seen:
            seen.add(key)
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
