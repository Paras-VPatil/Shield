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


class CapabilityInsights(BaseModel):
    complexity_score: int = Field(default=0, ge=0, le=100)
    decision_readiness_score: int = Field(default=0, ge=0, le=100)
    top_concepts: List[str] = Field(default_factory=list)
    investigation_actions: List[str] = Field(default_factory=list)
    service_improvements: List[str] = Field(default_factory=list)
    business_opportunities: List[str] = Field(default_factory=list)
    stakeholder_communications: List[str] = Field(default_factory=list)
    visualization_recommendations: List[str] = Field(default_factory=list)


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
    capability_insights: CapabilityInsights = Field(default_factory=CapabilityInsights)
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
