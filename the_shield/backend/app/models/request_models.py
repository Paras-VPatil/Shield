from typing import List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000)


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=200)


class MeetingCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)


class SpeakerSegment(BaseModel):
    speaker: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=4000)


class MeetingAnalyzeRequest(BaseModel):
    text: Optional[str] = Field(default="", max_length=20000)
    speaker_segments: List[SpeakerSegment] = Field(default_factory=list)


class TechStackRequest(BaseModel):
    scale: str = Field(default="Medium")
    budget: str = Field(default="Moderate")
    integrations: List[str] = Field(default_factory=list)


class RevisionRequest(BaseModel):
    accepted_insights: List[str] = Field(default_factory=list)
    edited_insights: List[str] = Field(default_factory=list)


class RebalanceRequest(BaseModel):
    sprint_velocity: int = Field(default=10)
    team_members: int = Field(default=3)
