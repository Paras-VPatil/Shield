from fastapi import APIRouter

from app.models.request_models import AnalyzeRequest
from app.models.response_models import AnalyzeResponse
from app.services.analysis_engine import run_requirement_analysis
from app.services.llm_service import LLMService

router = APIRouter(tags=["analysis"])
llm_service = LLMService()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_requirement(payload: AnalyzeRequest) -> AnalyzeResponse:
    analysis = run_requirement_analysis(payload.text, llm_service)
    return AnalyzeResponse(**analysis)
