from typing import Literal

from pydantic import BaseModel, Field


class UserDocument(BaseModel):
    id: str = Field(..., min_length=1)
    username: str = Field(..., min_length=3, max_length=50)
    password_salt: str = Field(..., min_length=1)
    password_hash: str = Field(..., min_length=1)
    created_at: str


class SessionDocument(BaseModel):
    token: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    created_at: str
    expires_at: str | None = None


class MinuteEntry(BaseModel):
    id: str = Field(..., min_length=1)
    source: Literal["text", "pdf"]
    text: str = ""
    created_at: str
    filename: str | None = None


class SpeakerNote(BaseModel):
    id: str = Field(..., min_length=1)
    speaker: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1)
    created_at: str


class AnalysisSnapshot(BaseModel):
    status: str
    message: str
    domains: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    resolved_now: list[str] = Field(default_factory=list)
    open_after_analysis: list[str] = Field(default_factory=list)


class AnalysisHistoryEntry(BaseModel):
    id: str = Field(..., min_length=1)
    created_at: str
    input_text: str = Field(..., min_length=1)
    analysis: AnalysisSnapshot


class MeetingDocument(BaseModel):
    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=3, max_length=200)
    owner_id: str = Field(..., min_length=1)
    created_at: str
    updated_at: str
    domains: list[str] = Field(default_factory=list)
    minutes: list[MinuteEntry] = Field(default_factory=list)
    analysis_history: list[AnalysisHistoryEntry] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    resolved_questions: list[str] = Field(default_factory=list)
    speaker_notes: list[SpeakerNote] = Field(default_factory=list)
