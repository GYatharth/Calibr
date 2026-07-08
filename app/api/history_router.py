"""
Resume Score History endpoint.

GET /history
  - Returns all scores for the current logged-in candidate
  - Shows JD, score, date, matched/missing skills
  - Auth required — candidates only see their own history
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.db import models
from app.api.auth import get_current_user

router = APIRouter(prefix="/history", tags=["history"])


class ScoreHistoryEntry(BaseModel):
    candidate_id: int
    jd_id: int
    composite_score: float
    skill_score: float
    semantic_score: float
    experience_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    candidate_summary: Optional[str] = None
    scored_at: datetime


class ScoreHistoryResponse(BaseModel):
    total_attempts: int
    best_score: float
    latest_score: float
    average_score: float
    history: list[ScoreHistoryEntry]


@router.get("", response_model=ScoreHistoryResponse)
def get_score_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Returns all scoring attempts for the current user.
    Works for both candidates (their own uploads) and
    recruiters (all candidates they've scored).
    Sorted by most recent first.
    """
    # Recruiters see candidates scored against JDs they own.
    # Candidates see only the score attempts tied to their own account
    # (Candidate.user_id, set at score-submission time).

    if current_user.role == "candidate":
        candidates = (
            db.query(models.Candidate)
            .filter(models.Candidate.user_id == current_user.id)
            .join(models.Score)
            .order_by(models.Score.computed_at.desc())
            .all()
        )
    else:
        # For recruiters: show candidates from their JDs
        jd_ids = [
            jd.id for jd in db.query(models.JobDescription).filter(
                models.JobDescription.owner_id == current_user.id,
                models.JobDescription.id != 1
            ).all()
        ]
        candidates = (
            db.query(models.Candidate)
            .filter(models.Candidate.jd_id.in_(jd_ids))
            .join(models.Score)
            .order_by(models.Score.computed_at.desc())
            .all()
        ) if jd_ids else []

    history = []
    for candidate in candidates:
        score = candidate.score
        if not score:
            continue

        summary = None
        if score.explanation:
            summary = score.explanation.candidate_summary

        history.append(ScoreHistoryEntry(
            candidate_id=candidate.id,
            jd_id=candidate.jd_id,
            composite_score=score.composite_score,
            skill_score=score.skill_match_score,
            semantic_score=score.semantic_score,
            experience_score=score.experience_score,
            matched_skills=score.matched_skills or [],
            missing_skills=score.missing_skills or [],
            candidate_summary=summary,
            scored_at=score.computed_at,
        ))

    if not history:
        return ScoreHistoryResponse(
            total_attempts=0,
            best_score=0,
            latest_score=0,
            average_score=0,
            history=[],
        )

    scores = [h.composite_score for h in history]
    return ScoreHistoryResponse(
        total_attempts=len(history),
        best_score=round(max(scores), 1),
        latest_score=round(history[0].composite_score, 1),
        average_score=round(sum(scores) / len(scores), 1),
        history=history,
    )
