import re
from collections import Counter

from app.models.response_models import RequirementItemAnalysis
from app.utils.helpers import unique_in_order

STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "as",
    "is",
    "are",
    "be",
    "by",
    "this",
    "that",
    "it",
    "from",
    "at",
    "into",
    "using",
    "use",
    "will",
    "must",
    "should",
    "can",
}

CONSTRAINT_TERMS = {
    "compliance",
    "audit",
    "secure",
    "security",
    "latency",
    "performance",
    "privacy",
    "reliability",
    "scalable",
    "availability",
    "risk",
    "regulatory",
}

DECISION_TERMS = {
    "decision",
    "decide",
    "decided",
    "approved",
    "chosen",
    "adopt",
    "select",
    "selected",
    "standardize",
    "must",
    "shall",
    "will",
}

SERVICE_IMPROVEMENT_MAP = {
    "security": "Define stronger authentication, session, and audit controls to reduce incidents.",
    "healthcare": "Add privacy-by-design checks and clinical workflow validations before release.",
    "analytics": "Introduce KPI dashboards to track requirement quality, risk, and delivery impact.",
    "payment": "Harden retry, reconciliation, and fraud workflows to reduce payment failures.",
    "booking": "Improve conflict handling and cancellation policy clarity to reduce support load.",
    "integration": "Introduce API contract versioning and monitoring to improve external reliability.",
}

BUSINESS_OPPORTUNITY_MAP = {
    "security": "Position enterprise-grade security and compliance reporting as a premium capability.",
    "healthcare": "Offer compliant healthcare workflows as a vertical product differentiator.",
    "analytics": "Package insights dashboards for leadership decision-making and upsell opportunities.",
    "payment": "Expand monetization with subscription tiers and conversion-focused payment UX.",
    "booking": "Enable dynamic pricing and optimization features to improve utilization and revenue.",
    "integration": "Expose partner APIs and marketplace integrations to unlock ecosystem growth.",
}


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]{1,}", text.lower())
    return [token for token in tokens if token not in STOP_WORDS]


def _top_concepts(text: str, limit: int = 8) -> list[str]:
    counter = Counter(_tokenize(text))
    return [word for word, _ in counter.most_common(limit)]


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


def _complexity_score(
    token_set: set[str],
    item_analyses: list[RequirementItemAnalysis],
    missing_fields: list[str],
    domain_gaps: list[str],
) -> int:
    gap_count = sum(1 for item in item_analyses if item.status == "gap_detected")
    incomplete_count = sum(1 for item in item_analyses if item.status == "incomplete")
    constraint_hits = len(token_set.intersection(CONSTRAINT_TERMS))
    score = 30 + (gap_count * 12) + (incomplete_count * 8) + (len(domain_gaps) * 3) + (constraint_hits * 4)
    score += min(len(missing_fields) * 3, 12)
    return _clamp_score(score)


def _decision_readiness_score(
    token_set: set[str],
    missing_fields: list[str],
    domain_gaps: list[str],
) -> int:
    decision_hits = len(token_set.intersection(DECISION_TERMS))
    ambiguity_penalty = (len(missing_fields) * 7) + (len(domain_gaps) * 3)
    score = 72 + (decision_hits * 6) - ambiguity_penalty
    return _clamp_score(score)


def _investigation_actions(
    missing_fields: list[str],
    domain_gaps: list[str],
    top_concepts: list[str],
) -> list[str]:
    actions: list[str] = []
    if missing_fields:
        actions.append(
            f"Clarify missing requirement fields ({', '.join(unique_in_order(missing_fields))}) before implementation."
        )
    for gap in domain_gaps[:3]:
        actions.append(f"Investigate unresolved gap: {gap}. Add measurable acceptance criteria.")
    if top_concepts:
        focus = ", ".join(top_concepts[:4])
        actions.append(f"Run root-cause analysis around high-impact concepts: {focus}.")
    if not actions:
        actions.append("Perform cross-functional review to validate assumptions and decision boundaries.")
    return unique_in_order(actions)


def _domain_opportunities(domains: list[str], mapping: dict[str, str], fallback: str) -> list[str]:
    opportunities = [mapping[domain] for domain in domains if domain in mapping]
    if not opportunities:
        opportunities = [fallback]
    return unique_in_order(opportunities)


def _stakeholder_communications(item_analyses: list[RequirementItemAnalysis], domains: list[str]) -> list[str]:
    notes: list[str] = []
    for item in item_analyses[:4]:
        actor = (item.parsed.actor or "Stakeholder").strip()
        action = (item.parsed.action or "review").strip()
        obj = (item.parsed.obj or "requirement scope").strip()
        notes.append(f"{actor.title()}: confirm '{action} {obj}' and approval criteria.")
    if domains:
        notes.append(
            f"Disseminate domain decisions ({', '.join(domains)}) via structured weekly requirement brief."
        )
    if not notes:
        notes.append("Publish a concise decision log with owners, dependencies, and due dates.")
    return unique_in_order(notes)


def build_capability_insights(
    text: str,
    item_analyses: list[RequirementItemAnalysis],
    missing_fields: list[str],
    domain_gaps: list[str],
    domains: list[str],
) -> dict:
    concepts = _top_concepts(text)
    token_set = set(_tokenize(text))
    complexity = _complexity_score(token_set, item_analyses, missing_fields, domain_gaps)
    decision_readiness = _decision_readiness_score(token_set, missing_fields, domain_gaps)

    return {
        "complexity_score": complexity,
        "decision_readiness_score": decision_readiness,
        "top_concepts": concepts,
        "investigation_actions": _investigation_actions(missing_fields, domain_gaps, concepts),
        "service_improvements": _domain_opportunities(
            domains=domains,
            mapping=SERVICE_IMPROVEMENT_MAP,
            fallback="Standardize requirement templates and QA gates to improve service predictability.",
        ),
        "business_opportunities": _domain_opportunities(
            domains=domains,
            mapping=BUSINESS_OPPORTUNITY_MAP,
            fallback="Use requirement intelligence metrics as a consulting and product optimization offering.",
        ),
        "stakeholder_communications": _stakeholder_communications(item_analyses, domains),
        "visualization_recommendations": [
            "Requirement status heatmap (complete/incomplete/gap_detected) across all extracted items.",
            "Trend chart of open vs resolved clarification questions per meeting iteration.",
            "Domain-wise risk radar linking detected gaps to service and business impact.",
        ],
        "sprint_plan": [],
        "proprietary_tool_suggestions": [],
    }
