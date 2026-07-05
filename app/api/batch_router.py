"""
Day 14: Batch upload + async processing.

POST /batch/score
  - Accepts: jd_id + list of resume texts (up to 100)
  - Creates a ScoringJob record to track progress
  - Processes resumes in the background (FastAPI BackgroundTasks)
  - Returns immediately with job_id so client can poll status

GET /batch/status/{job_id}
  - Returns current job status, progress count, and results so far

Design note: using FastAPI BackgroundTasks for v1 — sufficient for
hundreds of resumes without the infrastructure overhead of Celery+Redis.
Celery upgrade comes in Phase 5 (Days 17-19).
"""

import sys
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "scoring"))
sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))

from app.db.database import SessionLocal, get_db
from app.db import models
from app.api.auth import get_current_user

from parse_jd import parse_job_description
from parse_resume import parse_resume
from composite_score import compute_composite_score
from explainer import generate_explanation
from semantic_similarity import semantic_similarity_score

router = APIRouter(prefix="/batch", tags=["batch scoring"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class BatchScoreRequest(BaseModel):
    jd_id: int
    resume_texts: list[str]  # list of raw resume texts, max 100


class JobStatusResponse(BaseModel):
    job_id: int
    status: str
    total_resumes: int
    processed_resumes: int
    progress_pct: float
    completed_at: Optional[datetime] = None


# ── Background task ───────────────────────────────────────────────────────────
def process_batch(job_id: int, jd_id: int, resume_texts: list[str]):
    """
    Runs in the background after the API returns the job_id.
    Scores each resume independently, persists results, updates
    job progress after each one so the status endpoint reflects
    real-time progress.

    Uses its own DB session (not the request session, which is
    already closed by the time this runs).
    """
    db = SessionLocal()
    try:
        # Mark job as processing
        job = db.query(models.ScoringJob).filter(
            models.ScoringJob.id == job_id
        ).first()
        job.status = "processing"
        db.commit()

        # Load JD once — reuse for all resumes
        jd = db.query(models.JobDescription).filter(
            models.JobDescription.id == jd_id
        ).first()
        jd_data = parse_job_description(jd.raw_text)

        for i, resume_text in enumerate(resume_texts):
            try:
                # Score this resume
                resume_data = parse_resume(resume_text)
                sem_result = semantic_similarity_score(resume_data, jd_data)
                score_data = compute_composite_score(
                    resume_data, jd_data, sem_result["semantic_score"]
                )
                explanation = generate_explanation(score_data, jd_data)

                # Persist candidate
                candidate = models.Candidate(
                    jd_id=jd_id,
                    raw_resume_text=resume_text,
                    extracted_skills=resume_data["skills"],
                    extracted_experience=resume_data["experience"],
                    total_experience_months=resume_data["total_experience_months"],
                )
                db.add(candidate)
                db.flush()

                # Persist score
                score = models.Score(
                    candidate_id=candidate.id,
                    skill_match_score=score_data["skill_score"],
                    semantic_score=score_data["semantic_score"],
                    experience_score=score_data["experience_score"],
                    composite_score=score_data["composite_score"],
                    matched_skills=score_data["matched_skills"],
                    missing_skills=score_data["missing_skills"],
                    weights_used=score_data["weights_used"],
                )
                db.add(score)
                db.flush()

                # Persist explanation
                exp_record = models.Explanation(
                    score_id=score.id,
                    explanation_text=explanation,
                    missing_skills=score_data["missing_skills"],
                )
                db.add(exp_record)

                # Update progress
                job.processed_resumes = i + 1
                db.commit()

            except Exception as e:
                # One failed resume shouldn't stop the whole batch
                print(f"[warn] Resume {i+1} failed: {e}")
                job.processed_resumes = i + 1
                db.commit()
                continue

        # Mark job complete
        job.status = "done"
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        job = db.query(models.ScoringJob).filter(
            models.ScoringJob.id == job_id
        ).first()
        if job:
            job.status = "failed"
            db.commit()
        print(f"[error] Batch job {job_id} failed: {e}")
    finally:
        db.close()


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/score", status_code=202)
def batch_score(
    request: BatchScoreRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Submit a batch of resumes for scoring against a JD.
    Returns immediately with job_id — processing happens in background.
    202 Accepted means "received, processing started, not done yet."
    """
    if len(request.resume_texts) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 resumes per batch"
        )

    if len(request.resume_texts) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one resume required"
        )

    # Ownership check
    jd = db.query(models.JobDescription).filter(
        models.JobDescription.id == request.jd_id,
        models.JobDescription.owner_id == current_user.id,
    ).first()
    if not jd:
        raise HTTPException(
            status_code=404,
            detail="JD not found or not authorised"
        )

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

    # Kick off background processing
    background_tasks.add_task(
        process_batch,
        job_id=job.id,
        jd_id=request.jd_id,
        resume_texts=request.resume_texts,
    )

    return {
        "job_id": job.id,
        "status": "pending",
        "total_resumes": job.total_resumes,
        "message": f"Batch job started. Poll GET /batch/status/{job.id} for progress."
    }


@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Poll the status of a batch scoring job.
    Ownership enforced via the JD's owner_id.
    """
    job = db.query(models.ScoringJob).filter(
        models.ScoringJob.id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Ownership check via JD
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