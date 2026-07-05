"""
Day 15: Rankings endpoint.

GET /rankings/{jd_id}
  - Returns all candidates scored against this JD
  - Sorted by composite score descending (best fit first)
  - Includes signal breakdown per candidate
  - Auth required, ownership enforced

This is the core recruiter-facing view of Calibr.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.db import models
from app.api.auth import get_current_user

router = APIRouter(prefix="/rankings", tags=["rankings"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class CandidateRanking(BaseModel):
    rank: int
    candidate_id: int
    composite_score: float
    skill_score: float
    semantic_score: float
    experience_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    experience_gap: str
    explanation: Optional[str] = None
    scored_at: datetime


class RankingsResponse(BaseModel):
    jd_id: int
    total_candidates: int
    candidates: list[CandidateRanking]


# ── Endpoint ──────────────────────────────────────────────────────────────────
@router.get("/{jd_id}", response_model=RankingsResponse)
def get_rankings(
    jd_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get ranked candidates for a JD, sorted by composite score.
    Ownership enforced — recruiters only see their own candidates.
    """
    # Ownership check
    jd = db.query(models.JobDescription).filter(
        models.JobDescription.id == jd_id,
        models.JobDescription.owner_id == current_user.id,
    ).first()
    if not jd:
        raise HTTPException(
            status_code=404,
            detail="JD not found or not authorised"
        )

    # Fetch all candidates for this JD that have been scored
    candidates = (
        db.query(models.Candidate)
        .filter(models.Candidate.jd_id == jd_id)
        .all()
    )

    if not candidates:
        return RankingsResponse(
            jd_id=jd_id,
            total_candidates=0,
            candidates=[],
        )

    # Build ranked list
    ranked = []
    for candidate in candidates:
        score = candidate.score
        if not score:
            continue  # skip candidates not yet scored

        explanation_text = None
        if score.explanation:
            explanation_text = score.explanation.explanation_text

        ranked.append({
            "candidate_id": candidate.id,
            "composite_score": score.composite_score,
            "skill_score": score.skill_match_score,
            "semantic_score": score.semantic_score,
            "experience_score": score.experience_score,
            "matched_skills": score.matched_skills or [],
            "missing_skills": score.missing_skills or [],
            "experience_gap": candidate.score.missing_skills and "check_score" or "n/a",
            "explanation": explanation_text,
            "scored_at": score.computed_at,
        })

    # Sort by composite score descending
    ranked.sort(key=lambda x: x["composite_score"], reverse=True)

    # Add rank numbers
    result = []
    for i, r in enumerate(ranked, 1):
        result.append(CandidateRanking(rank=i, **r))

    return RankingsResponse(
        jd_id=jd_id,
        total_candidates=len(result),
        candidates=result,
    )