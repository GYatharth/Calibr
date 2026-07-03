"""
Day 13: Job Description endpoints.

POST /jd        — upload a JD (auth required, scoped to current user)
GET  /jd        — list all JDs belonging to the current user
GET  /jd/{id}   — get one JD by ID (ownership checked)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.db import models
from app.api.auth import get_current_user

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))
from parse_jd import parse_job_description

router = APIRouter(prefix="/jd", tags=["job descriptions"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class JDCreateRequest(BaseModel):
    raw_text: str


class JDResponse(BaseModel):
    id: int
    raw_text: str
    required_skills: Optional[list] = []
    required_experience_years: Optional[int] = None

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("", response_model=JDResponse, status_code=201)
def create_jd(
    request: JDCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Upload a new job description. Automatically parses required skills
    and experience years from the raw text using the Day 2 parser.
    Scoped to the currently logged-in user.
    """
    parsed = parse_job_description(request.raw_text)

    jd = models.JobDescription(
        owner_id=current_user.id,
        raw_text=request.raw_text,
        required_skills=parsed["required_skills"],
        required_experience_years=parsed["required_experience_years"],
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return jd


@router.get("", response_model=list[JDResponse])
def list_jds(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    List all JDs belonging to the current user.
    Users cannot see each other's JDs — ownership enforced here.
    """
    return db.query(models.JobDescription).filter(
        models.JobDescription.owner_id == current_user.id
    ).all()


@router.get("/{jd_id}", response_model=JDResponse)
def get_jd(
    jd_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get one JD by ID. Returns 404 if not found, 403 if it belongs
    to a different user — never leaks that another user's JD exists.
    """
    jd = db.query(models.JobDescription).filter(
        models.JobDescription.id == jd_id
    ).first()

    if not jd:
        raise HTTPException(status_code=404, detail="JD not found")

    # Ownership check — this is the IDOR prevention from the IG post
    if jd.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to access this JD")

    return jd