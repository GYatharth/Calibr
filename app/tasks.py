"""
Day 17-18: Celery tasks — updated with candidate summary generation.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "scoring"))
sys.path.insert(0, str(Path(__file__).parent / "parsing"))

from app.celery_app import celery_app
from app.db.database import SessionLocal
from app.db import models

from parse_jd import parse_job_description
from parse_resume import parse_resume
from composite_score import compute_composite_score
from explainer import generate_explanation, generate_candidate_summary
from semantic_similarity import semantic_similarity_score


@celery_app.task(bind=True, max_retries=3)
def score_resume_batch(self, job_id: int, jd_id: int, resume_texts: list):
    """
    Celery task: score a batch of resumes against a JD.
    Now also generates a one-line AI summary per candidate.
    """
    db = SessionLocal()
    try:
        job = db.query(models.ScoringJob).filter(
            models.ScoringJob.id == job_id
        ).first()
        if not job:
            raise ValueError(f"ScoringJob {job_id} not found")

        job.status = "processing"
        db.commit()

        jd = db.query(models.JobDescription).filter(
            models.JobDescription.id == jd_id
        ).first()
        if not jd:
            raise ValueError(f"JobDescription {jd_id} not found")

        jd_data = parse_job_description(jd.raw_text)

        for i, resume_text in enumerate(resume_texts):
            try:
                resume_data = parse_resume(resume_text)
                sem_result = semantic_similarity_score(resume_data, jd_data)
                score_data = compute_composite_score(
                    resume_data, jd_data, sem_result["semantic_score"]
                )
                explanation = generate_explanation(score_data, jd_data)
                summary = generate_candidate_summary(score_data, resume_data)

                candidate = models.Candidate(
                    jd_id=jd_id,
                    raw_resume_text=resume_text,
                    extracted_skills=resume_data["skills"],
                    extracted_experience=resume_data["experience"],
                    total_experience_months=resume_data["total_experience_months"],
                )
                db.add(candidate)
                db.flush()

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

                exp_record = models.Explanation(
                    score_id=score.id,
                    explanation_text=explanation,
                    candidate_summary=summary,
                    missing_skills=score_data["missing_skills"],
                )
                db.add(exp_record)

                job.processed_resumes = i + 1
                db.commit()

            except Exception as e:
                print(f"[warn] Resume {i+1} failed: {e}")
                job.processed_resumes = i + 1
                db.commit()
                continue

        job.status = "done"
        job.completed_at = datetime.utcnow()
        db.commit()

        return {
            "job_id": job_id,
            "status": "done",
            "processed": job.processed_resumes
        }

    except Exception as e:
        try:
            job = db.query(models.ScoringJob).filter(
                models.ScoringJob.id == job_id
            ).first()
            if job:
                job.status = "failed"
                db.commit()
        except Exception:
            pass

        raise self.retry(exc=e, countdown=5)

    finally:
        db.close()