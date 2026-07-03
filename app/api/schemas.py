"""
Pydantic schemas — request and response shapes for the API.

Keeping schemas separate from DB models is intentional:
- DB models (models.py) define what's stored in PostgreSQL
- Schemas define what comes IN and goes OUT through the API
They often look similar but serve different purposes.
"""

from pydantic import BaseModel
from typing import Optional


# ── Request schemas ───────────────────────────────────────────────────────────

class JDRequest(BaseModel):
    """Request body for uploading a job description."""
    raw_text: str


class SingleScoreRequest(BaseModel):
    """Request body for scoring one resume against a JD."""
    jd_text: str
    resume_text: str  # raw extracted text (client handles PDF extraction for now)


# ── Response schemas ──────────────────────────────────────────────────────────

class SignalBreakdown(BaseModel):
    skill_contribution: float
    semantic_contribution: float
    experience_contribution: float


class ScoreResponse(BaseModel):
    """Full scoring result returned to the client."""
    composite_score: float
    skill_score: float
    semantic_score: float
    experience_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    experience_gap: str
    signal_breakdown: SignalBreakdown
    weights_used: dict
    explanation: str


class HealthResponse(BaseModel):
    status: str