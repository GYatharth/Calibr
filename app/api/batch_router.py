"""
Day 18: Batch upload endpoint — upgraded to Celery.

Same interface as Day 14, but now uses Celery tasks instead of
FastAPI BackgroundTasks. The API still returns immediately with
a job_id — but now processing happens in a separate Celery worker
process, not in the same process as the API server.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.db import models
from app.api.auth import get_current_user
from app.tasks import score_resume_batch

router = APIRouter(prefix="/batch", tags=["batch scoring"])


class BatchScoreRequest(BaseModel):
    jd_id: int
    resume_texts: list[str]


class JobStatusResponse(BaseModel):
    job_id: int
    status: str
    total_resumes: int
    processed_resumes: int
    progress_pct: float
    completed_at: Optional[datetime] = None


@router.post("/score", status_code=202)
def batch_score(
    request: BatchScoreRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Submit batch of resumes for Celery-powered scoring.
    Returns immediately with job_id — Celery worker handles the rest.
    """
    if len(request.resume_texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 resumes per batch")
    if len(request.resume_texts) == 0:
        raise HTTPException(status_code=400, detail="At least one resume required")

    # Ownership check
    jd = db.query(models.JobDescription).filter(
        models.JobDescription.id == request.jd_id,
        models.JobDescription.owner_id == current_user.id,
    ).first()
    if not jd:
        raise HTTPException(status_code=404, detail="JD not found or not authorised")

    # Create job record
    job = models.ScoringJob(
        jd_id=request.jd_id,
        status="pending",
        total_resumes=len(request.resume_texts),
        processed_resumes=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Send task to Celery worker
    score_resume_batch.delay(
        job_id=job.id,
        jd_id=request.jd_id,
        resume_texts=request.resume_texts,
    )

    return {
        "job_id": job.id,
        "status": "pending",
        "total_resumes": job.total_resumes,
        "message": f"Batch job queued. Poll GET /batch/status/{job.id} for progress."
    }


@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Poll batch job status — same as Day 14 version."""
    job = db.query(models.ScoringJob).filter(
        models.ScoringJob.id == job_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    jd = db.query(models.JobDescription).filter(
        models.JobDescription.id == job.jd_id,
        models.JobDescription.owner_id == current_user.id,
    ).first()
    if not jd:
        raise HTTPException(status_code=403, detail="Not authorised to view this job")

    progress_pct = (
        round((job.processed_resumes / job.total_resumes) * 100, 1)
        if job.total_resumes > 0 else 0.0
    )

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        total_resumes=job.total_resumes,
        processed_resumes=job.processed_resumes,
        progress_pct=progress_pct,
        completed_at=job.completed_at,
    )