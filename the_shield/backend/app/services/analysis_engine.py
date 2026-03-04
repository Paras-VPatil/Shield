from typing import Optional

from app.models.response_models import ParseResult, RequirementItemAnalysis
from app.services.capability_insight_service import build_capability_insights
from app.services.domain_detector import detect_domains
from app.services.gap_detector import analyze_requirement_completeness
from app.services.llm_service import LLMService
from app.services.question_generator import generate_questions
from app.services.requirement_extractor import extract_requirements
from app.services.requirement_parser import parse_requirement
from app.utils.helpers import unique_in_order


def run_requirement_analysis(
    text: str,
    llm_service: LLMService,
    context_text: Optional[str] = None,
) -> dict:
    requirement_items = extract_requirements(text)
    if not requirement_items:
        requirement_items = [text.strip()]

    item_analyses: list[RequirementItemAnalysis] = []
    status_order = {"complete": 0, "incomplete": 1, "gap_detected": 2}
    overall_status = "complete"
    all_missing_fields: list[str] = []
    all_domain_gaps: list[str] = []

    for requirement in requirement_items:
        parsed_item = parse_requirement(requirement)
        completeness_item = analyze_requirement_completeness(requirement, parsed_item)
        detected_domains_item = detect_domains(requirement)
        questions_item = generate_questions(
            missing_fields=completeness_item["missing_fields"],
            domain_gaps=completeness_item["domain_gaps"],
            requirement_text=requirement,
            domains=detected_domains_item,
        )
        item_analyses.append(
            RequirementItemAnalysis(
                requirement=requirement,
                status=completeness_item["status"],
                message=completeness_item["message"],
                parsed=ParseResult(**parsed_item),
                missing_fields=completeness_item["missing_fields"],
                domain_gaps=completeness_item["domain_gaps"],
                questions=questions_item,
            )
        )

        if status_order[completeness_item["status"]] > status_order[overall_status]:
            overall_status = completeness_item["status"]

        all_missing_fields.extend(completeness_item["missing_fields"])
        all_domain_gaps.extend(completeness_item["domain_gaps"])

    all_missing_fields = unique_in_order(all_missing_fields)
    all_domain_gaps = unique_in_order(all_domain_gaps)
    context_payload = f"{context_text.strip()}\n\n{text.strip()}" if context_text and context_text.strip() else text
    detected_domains = detect_domains(context_payload)
    questions = generate_questions(
        missing_fields=all_missing_fields,
        domain_gaps=all_domain_gaps,
        requirement_text=context_payload,
        domains=detected_domains,
    )
    capability_insights = build_capability_insights(
        text=context_payload,
        item_analyses=item_analyses,
        missing_fields=all_missing_fields,
        domain_gaps=all_domain_gaps,
        domains=detected_domains,
    )
    parsed = item_analyses[0].parsed.model_dump() if item_analyses else parse_requirement(text)
    message = (
        f"Analyzed {len(requirement_items)} requirement(s). "
        f"Overall status: {overall_status}."
    )
    llm_summary = llm_service.summarize(
        text=context_payload,
        parsed=parsed,
        status=overall_status,
        missing_fields=all_missing_fields,
        domain_gaps=all_domain_gaps,
        questions=questions,
    )

    return {
        "status": overall_status,
        "message": message,
        "parsed": ParseResult(**parsed),
        "missing_fields": all_missing_fields,
        "domain_gaps": all_domain_gaps,
        "questions": questions,
        "extracted_requirements": requirement_items,
        "item_analyses": item_analyses,
        "capability_insights": capability_insights,
        "llm_summary": llm_summary,
        "domains": detected_domains,
    }
