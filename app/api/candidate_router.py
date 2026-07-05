"""
Day 16: Candidate score breakdown endpoint.

GET /candidates/{candidate_id}/breakdown
  - Returns full score breakdown for one candidate
  - Shows all three signals separately + explanation
  - This is the "why did this candidate rank here" view
  - Auth required, ownership enforced via JD
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.db import models
from app.api.auth import get_current_user

router = APIRouter(prefix="/candidates", tags=["candidates"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class ScoreBreakdownResponse(BaseModel):
    candidate_id: int
    jd_id: int
    composite_score: float
    signal_breakdown: dict
    matched_skills: list[str]
    missing_skills: list[str]
    total_experience_months: int
    explanation: Optional[str] = None
    scored_at: datetime


# ── Endpoint ──────────────────────────────────────────────────────────────────
@router.get("/{candidate_id}/breakdown",
            response_model=ScoreBreakdownResponse)
def get_score_breakdown(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get full score breakdown for one candidate.
    Shows each signal score separately so the recruiter understands
    exactly why the candidate ranked where they did.
    """
    candidate = db.query(models.Candidate).filter(
        models.Candidate.id == candidate_id
    ).first()

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Ownership check via JD
    jd = db.query(models.JobDescription).filter(
        models.JobDescription.id == candidate.jd_id,
        models.JobDescription.owner_id == current_user.id,
    ).first()
    if not jd:
        raise HTTPException(
            status_code=403,
            detail="Not authorised to view this candidate"
        )

    score = candidate.score
    if not score:
        raise HTTPException(
            status_code=404,
            detail="This candidate has not been scored yet"
        )

    explanation_text = None
    if score.explanation:
        explanation_text = score.explanation.explanation_text

    return ScoreBreakdownResponse(
        candidate_id=candidate.id,
        jd_id=candidate.jd_id,
        composite_score=score.composite_score,
        signal_breakdown={
            "skill_match": {
                "score": score.skill_match_score,
                "weight": score.weights_used.get("w1_skill", 0.45),
                "contribution": round(
                    score.skill_match_score *
                    score.weights_used.get("w1_skill", 0.45), 2
                ),
            },
            "semantic_similarity": {
                "score": score.semantic_score,
                "weight": score.weights_used.get("w2_semantic", 0.35),
                "contribution": round(
                    score.semantic_score *
                    score.weights_used.get("w2_semantic", 0.35), 2
                ),
            },
            "experience_relevance": {
                "score": score.experience_score,
                "weight": score.weights_used.get("w3_experience", 0.20),
                "contribution": round(
                    score.experience_score *
                    score.weights_used.get("w3_experience", 0.20), 2
                ),
            },
        },
        matched_skills=score.matched_skills or [],
        missing_skills=score.missing_skills or [],
        total_experience_months=candidate.total_experience_months or 0,
        explanation=explanation_text,
        scored_at=score.computed_at,
    )