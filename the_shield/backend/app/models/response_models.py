from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ParseResult(BaseModel):
    actor: Optional[str] = None
    action: Optional[str] = None
    obj: Optional[str] = None
    conditions: Optional[str] = None


class RequirementItemAnalysis(BaseModel):
    requirement: str
    status: Literal["complete", "incomplete", "gap_detected"]
    message: str
    parsed: ParseResult
    missing_fields: List[str] = Field(default_factory=list)
    domain_gaps: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    status: Literal["complete", "incomplete", "gap_detected"]
    message: str
    parsed: ParseResult
    missing_fields: List[str] = Field(default_factory=list)
    domain_gaps: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    extracted_requirements: List[str] = Field(default_factory=list)
    item_analyses: List[RequirementItemAnalysis] = Field(default_factory=list)
    llm_summary: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class UserInfoResponse(BaseModel):
    id: str
    username: str


class MeetingSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MeetingDetailResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    domains: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    resolved_questions: List[str] = Field(default_factory=list)
    minutes: List[dict] = Field(default_factory=list)
    analysis_history: List[dict] = Field(default_factory=list)


class MeetingAnalyzeResponse(AnalyzeResponse):
    meeting_id: str
    open_questions: List[str] = Field(default_factory=list)
    resolved_questions: List[str] = Field(default_factory=list)
