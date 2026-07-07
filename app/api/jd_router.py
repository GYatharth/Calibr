"""
Job Description endpoints — updated with public listing for candidates.
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


class JDCreateRequest(BaseModel):
    raw_text: str


class JDResponse(BaseModel):
    id: int
    raw_text: str
    required_skills: Optional[list] = []
    required_experience_years: Optional[int] = None

    class Config:
        from_attributes = True


@router.post("", response_model=JDResponse, status_code=201)
def create_jd(
    request: JDCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
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


@router.get("/public/all", response_model=list[JDResponse])
def list_all_jds_public(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Returns all job descriptions across all recruiters.
    Used by candidates to browse available roles.
    Auth required but not ownership-scoped.
    Excludes the default placeholder JD (id=1).
    """
    return db.query(models.JobDescription).filter(
        models.JobDescription.id != 1
    ).order_by(models.JobDescription.created_at.desc()).all()


@router.get("", response_model=list[JDResponse])
def list_jds(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    List all JDs belonging to the current user.
    Ownership enforced — recruiters only see their own JDs.
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
    jd = db.query(models.JobDescription).filter(
        models.JobDescription.id == jd_id
    ).first()

    if not jd:
        raise HTTPException(status_code=404, detail="JD not found")

    if jd.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to access this JD")

    return jd