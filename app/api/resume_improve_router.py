"""
AI Resume Improvement endpoint — comprehensive ATS optimization.
"""

import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "scoring"))
sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))

from app.db.database import get_db
from app.db import models
from app.api.auth import get_current_user
from explainer import generate_resume_improvements
from parse_resume import parse_resume
from parse_jd import parse_job_description

router = APIRouter(prefix="/improve", tags=["resume improvement"])


class BulletRewrite(BaseModel):
    original: str
    improved: str
    reason: str


class MissingKeyword(BaseModel):
    keyword: str
    suggestion: str


class PriorityAction(BaseModel):
    priority: int
    action: str
    impact: str


class ResumeImprovementResponse(BaseModel):
    candidate_id: int
    composite_score: float
    bullet_rewrites: list[BulletRewrite] = []
    missing_keywords: list[MissingKeyword] = []
    missing_sections: list[str] = []
    quick_wins: list[str] = []
    priority_plan: list[PriorityAction] = []


@router.get("/{candidate_id}", response_model=ResumeImprovementResponse)
def get_resume_improvements(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
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

    resume_data = parse_resume(candidate.raw_resume_text or "")
    jd_data = parse_job_description(jd.raw_text) if jd else {}

    score_data = {
        "composite_score": score.composite_score,
        "matched_skills": score.matched_skills or [],
        "missing_skills": score.missing_skills or [],
    }

    result = generate_resume_improvements(
        resume_data, score_data, jd_data,
        resume_text=candidate.raw_resume_text or ""
    )

    return ResumeImprovementResponse(
        candidate_id=candidate_id,
        composite_score=score.composite_score,
        bullet_rewrites=[BulletRewrite(**b) for b in result.get("bullet_rewrites", [])],
        missing_keywords=[MissingKeyword(**k) for k in result.get("missing_keywords", [])],
        missing_sections=result.get("missing_sections", []),
        quick_wins=result.get("quick_wins", []),
        priority_plan=[PriorityAction(**p) for p in result.get("priority_plan", [])],
    )
