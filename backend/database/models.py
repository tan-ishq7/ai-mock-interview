"""
Pydantic models that mirror the Supabase / Postgres tables.

These are used for request/response validation and internal data passing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Candidate
# ---------------------------------------------------------------------------
class Candidate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    email: str
    resume_raw_text: str = ""
    resume_sections: dict[str, Any] = Field(default_factory=dict)
    identified_field: str = ""
    primary_project: dict[str, Any] = Field(default_factory=dict)
    secondary_project: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Interview Session
# ---------------------------------------------------------------------------
class InterviewSession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    current_phase: int = 1
    status: str = "in_progress"  # in_progress | completed | cancelled


# ---------------------------------------------------------------------------
# Conversation Message
# ---------------------------------------------------------------------------
class ConversationMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    phase: int
    role: str  # system | assistant | user
    content: str
    depth_level: Optional[int] = None
    is_hint: bool = False
    hint_recovery: Optional[bool] = None
    anxiety_detected: bool = False


# ---------------------------------------------------------------------------
# ML Question (knowledge-base entry)
# ---------------------------------------------------------------------------
class MLQuestion(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    question: str
    answer: str
    category: str = ""
    source: str = ""


# ---------------------------------------------------------------------------
# Evaluation (per-phase scoring)
# ---------------------------------------------------------------------------
class Evaluation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    phase: int
    score: float = 0.0
    max_depth_reached: int = 0
    hints_given: int = 0
    hints_recovered: int = 0
    factual_correct: int = 0
    factual_total: int = 0
    behavioral_visionary: float = 0.0
    behavioral_grounded: float = 0.0
    behavioral_teamplayer: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Report (final interview report)
# ---------------------------------------------------------------------------
class Report(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    candidate_id: UUID
    overall_score: float = 0.0
    phase_scores: dict[str, Any] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    report_text: str = ""
