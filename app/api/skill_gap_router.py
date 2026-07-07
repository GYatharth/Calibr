"""
Skill Gap Analysis endpoint.

GET /skill-gap/{candidate_id}
  - Returns missing skills with learning recommendations
  - Auth required, ownership enforced
"""

import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent / "scoring"))
sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))

from app.db.database import get_db
from app.db import models
from app.api.auth import get_current_user
from explainer import generate_skill_recommendations
from parse_jd import parse_job_description

router = APIRouter(prefix="/skill-gap", tags=["skill gap"])


class SkillRecommendation(BaseModel):
    skill: str
    why_important: str
    search_queries: list[str]


class SkillGapResponse(BaseModel):
    candidate_id: int
    missing_skills: list[str]
    matched_skills: list[str]
    recommendations: list[SkillRecommendation]


@router.get("/{candidate_id}", response_model=SkillGapResponse)
def get_skill_gap(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    candidate = db.query(models.Candidate).filter(
        models.Candidate.id == candidate_id
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Ownership check
    jd = db.query(models.JobDescription).filter(
        models.JobDescription.id == candidate.jd_id,
        models.JobDescription.owner_id == current_user.id,
    ).first()
    if not jd:
        raise HTTPException(status_code=403, detail="Not authorised")

    score = candidate.score
    if not score:
        raise HTTPException(status_code=404, detail="Candidate not yet scored")

    missing = score.missing_skills or []
    matched = score.matched_skills or []
    jd_data = parse_job_description(jd.raw_text)

    recommendations = generate_skill_recommendations(missing, jd_data)

    return SkillGapResponse(
        candidate_id=candidate_id,
        missing_skills=missing,
        matched_skills=matched,
        recommendations=[SkillRecommendation(**r) for r in recommendations],
    )


@router.get("/candidate/{candidate_id}", response_model=SkillGapResponse)
def get_skill_gap_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Skill gap for candidates — no JD ownership check.
    NOTE: Candidate records have no owning-user link in the schema, so this
    does not actually verify the caller owns candidate_id (known IDOR gap).
    """
    candidate = db.query(models.Candidate).filter(
        models.Candidate.id == candidate_id
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    score = candidate.score
    if not score:
        raise HTTPException(status_code=404, detail="Candidate not yet scored")

    jd = db.query(models.JobDescription).filter(
        models.JobDescription.id == candidate.jd_id
    ).first()

    missing = score.missing_skills or []
    matched = score.matched_skills or []
    jd_data = parse_job_description(jd.raw_text) if jd else {}

    recommendations = generate_skill_recommendations(missing, jd_data)

    return SkillGapResponse(
        candidate_id=candidate_id,
        missing_skills=missing,
        matched_skills=matched,
        recommendations=[SkillRecommendation(**r) for r in recommendations],
    )