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
    questions: List[dict] = Field(default_factory=list)
    classification: Optional[str] = Field(default="Functional")
    moscow_priority: Optional[str] = Field(default="Should Have")


class SprintTask(BaseModel):
    task: str
    story_points: int = Field(default=1, ge=1)
    status: Literal["todo", "in_progress", "done"] = "todo"

class Sprint(BaseModel):
    number: int
    goal: str
    timeline: str
    tasks: List[SprintTask] = Field(default_factory=list)

class ToolSuggestion(BaseModel):
    name: str
    category: str
    reasoning: Optional[str] = None

class CapabilityInsights(BaseModel):
    complexity_score: int = Field(default=0, ge=0, le=100)
    decision_readiness_score: int = Field(default=0, ge=0, le=100)
    top_concepts: List[str] = Field(default_factory=list)
    investigation_actions: List[str] = Field(default_factory=list)
    service_improvements: List[str] = Field(default_factory=list)
    business_opportunities: List[str] = Field(default_factory=list)
    stakeholder_communications: List[str] = Field(default_factory=list)
    visualization_recommendations: List[str] = Field(default_factory=list)
    key_decisions: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    dependency_map: List[str] = Field(default_factory=list)
    stakeholder_impact: List[str] = Field(default_factory=list)
    sprint_plan: List[Sprint] = Field(default_factory=list)
    proprietary_tool_suggestions: List[ToolSuggestion] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    status: Literal["complete", "incomplete", "gap_detected"]
    message: str
    parsed: ParseResult
    missing_fields: List[str] = Field(default_factory=list)
    domain_gaps: List[str] = Field(default_factory=list)
    questions: List[dict] = Field(default_factory=list)
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

class RevisionResponse(BaseModel):
    meeting_id: str
    previous_id: str | None = None
    current_id: str
    added_requirements: List[str] = Field(default_factory=list)
    removed_requirements: List[str] = Field(default_factory=list)
    added_questions: List[str] = Field(default_factory=list)
    removed_questions: List[str] = Field(default_factory=list)
    status_changed: bool = False
    old_status: str | None = None
    new_status: str | None = None
