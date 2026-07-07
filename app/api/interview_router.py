"""
AI Interview Question Generator.

GET /interview/{candidate_id}
  - Generates tailored interview questions for a candidate
  - Based on their score data, matched/missing skills, and JD
  - Auth required, ownership enforced via JD
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
from explainer import generate_interview_questions
from parse_jd import parse_job_description
from parse_resume import parse_resume

router = APIRouter(prefix="/interview", tags=["interview"])


class InterviewQuestionsResponse(BaseModel):
    candidate_id: int
    composite_score: float
    technical: list[str]
    gap: list[str]
    behavioral: list[str]


@router.get("/{candidate_id}", response_model=InterviewQuestionsResponse)
def get_interview_questions(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Generate tailored interview questions for a candidate.
    Ownership enforced via the JD.
    """
    candidate = db.query(models.Candidate).filter(
        models.Candidate.id == candidate_id
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Recruiters may only view questions for candidates against their own
    # JDs. Candidates may view questions for any candidate record (they
    # aren't linked to a JD by ownership).
    jd_query = db.query(models.JobDescription).filter(
        models.JobDescription.id == candidate.jd_id
    )
    if current_user.role == "recruiter":
        jd_query = jd_query.filter(models.JobDescription.owner_id == current_user.id)
    jd = jd_query.first()
    if not jd:
        raise HTTPException(status_code=403, detail="Not authorised")

    score = candidate.score
    if not score:
        raise HTTPException(status_code=404, detail="Candidate not yet scored")

    # Build data dicts for the generator
    score_data = {
        "composite_score": score.composite_score,
        "matched_skills": score.matched_skills or [],
        "missing_skills": score.missing_skills or [],
    }
    jd_data = parse_job_description(jd.raw_text)
    resume_data = {
        "total_experience_months": candidate.total_experience_months or 0,
        "skills": candidate.extracted_skills or [],
        "experience": candidate.extracted_experience or [],
    }

    questions = generate_interview_questions(score_data, jd_data, resume_data)

    return InterviewQuestionsResponse(
        candidate_id=candidate_id,
        composite_score=score.composite_score,
        technical=questions.get("technical", []),
        gap=questions.get("gap", []),
        behavioral=questions.get("behavioral", []),
    )