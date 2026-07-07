"""
Recruiter Notes & Shortlisting endpoints.

PATCH /candidates/{candidate_id}/status
  - Update candidate status: pending / shortlisted / rejected
  - Auth required, ownership enforced via JD

PATCH /candidates/{candidate_id}/notes
  - Add or update recruiter notes for a candidate
  - Auth required, ownership enforced via JD
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.db import models
from app.api.auth import get_current_user

router = APIRouter(prefix="/candidates", tags=["notes"])


class StatusUpdate(BaseModel):
    status: str  # pending / shortlisted / rejected


class NotesUpdate(BaseModel):
    notes: str


class CandidateStatusResponse(BaseModel):
    candidate_id: int
    status: str
    recruiter_notes: Optional[str] = None

    class Config:
        from_attributes = True


def get_candidate_with_auth(candidate_id: int, db: Session, current_user: models.User):
    """Shared ownership check for candidate endpoints."""
    candidate = db.query(models.Candidate).filter(
        models.Candidate.id == candidate_id
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    jd = db.query(models.JobDescription).filter(
        models.JobDescription.id == candidate.jd_id,
        models.JobDescription.owner_id == current_user.id,
    ).first()
    if not jd:
        raise HTTPException(status_code=403, detail="Not authorised")

    return candidate


@router.patch("/{candidate_id}/status", response_model=CandidateStatusResponse)
def update_status(
    candidate_id: int,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update candidate shortlisting status."""
    if body.status not in ["pending", "shortlisted", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be: pending, shortlisted, or rejected"
        )

    candidate = get_candidate_with_auth(candidate_id, db, current_user)
    candidate.status = body.status
    db.commit()
    db.refresh(candidate)

    return CandidateStatusResponse(
        candidate_id=candidate.id,
        status=candidate.status,
        recruiter_notes=candidate.recruiter_notes,
    )


@router.patch("/{candidate_id}/notes", response_model=CandidateStatusResponse)
def update_notes(
    candidate_id: int,
    body: NotesUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Add or update recruiter notes for a candidate."""
    candidate = get_candidate_with_auth(candidate_id, db, current_user)
    candidate.recruiter_notes = body.notes
    db.commit()
    db.refresh(candidate)

    return CandidateStatusResponse(
        candidate_id=candidate.id,
        status=candidate.status,
        recruiter_notes=candidate.recruiter_notes,
    )