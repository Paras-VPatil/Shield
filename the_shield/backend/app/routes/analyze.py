from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.models.request_models import AnalyzeRequest
from app.models.response_models import AnalyzeResponse
from app.services.analysis_engine import run_requirement_analysis
from app.services.llm_service import LLMService
from app.services.meeting_service import _extract_pdf_text

router = APIRouter(tags=["analysis"])
llm_service = LLMService()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_requirement(payload: AnalyzeRequest) -> AnalyzeResponse:
    analysis = run_requirement_analysis(payload.text, llm_service)
    return AnalyzeResponse(**analysis)


@router.post("/extract/pdf")
async def extract_pdf_endpoint(file: UploadFile = File(...)) -> dict:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported.")
    content = await file.read()
    try:
        text = _extract_pdf_text(content)
        return {"filename": file.filename, "text": text}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
