"""
Day 20: Single-resume scoring endpoint with rate limiting and candidate summary.
"""

import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent / "scoring"))
sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))

from app.api.schemas import SingleScoreRequest, ScoreResponse, SignalBreakdown
from app.api.auth import get_current_user
from app.api.rate_limiter import limiter
from app.db.database import get_db
from app.db import models

from parse_jd import parse_job_description
from parse_resume import parse_resume
from composite_score import compute_composite_score
from explainer import generate_explanation, generate_candidate_summary
from semantic_similarity import semantic_similarity_score

router = APIRouter(prefix="/score", tags=["scoring"])


@router.post("", response_model=ScoreResponse)
@limiter.limit("10/minute")
def score_resume(
    request: Request,
    body: SingleScoreRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Score one resume against one job description.
    Rate limited: 10 requests/minute per IP.
    """
    try:
        # Ownership check — IDOR prevention
        jd = db.query(models.JobDescription).filter(
            models.JobDescription.id == body.jd_id,
            models.JobDescription.owner_id == current_user.id,
        ).first()
        if not jd:
            raise HTTPException(
                status_code=404,
                detail="JD not found or not authorised"
            )

        jd_data = parse_job_description(jd.raw_text)
        resume_data = parse_resume(body.resume_text)

        sem_result = semantic_similarity_score(resume_data, jd_data)
        score_data = compute_composite_score(
            resume_data, jd_data, sem_result["semantic_score"]
        )

        # Generate explanation and one-line summary
        explanation = generate_explanation(score_data, jd_data)
        summary = generate_candidate_summary(score_data, resume_data)

        candidate = models.Candidate(
            jd_id=body.jd_id,
            raw_resume_text=body.resume_text,
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
        db.commit()

        return ScoreResponse(
            composite_score=score_data["composite_score"],
            skill_score=score_data["skill_score"],
            semantic_score=score_data["semantic_score"],
            experience_score=score_data["experience_score"],
            matched_skills=score_data["matched_skills"],
            missing_skills=score_data["missing_skills"],
            experience_gap=score_data["experience_gap"],
            signal_breakdown=SignalBreakdown(
                **score_data["signal_breakdown"]
            ),
            weights_used=score_data["weights_used"],
            explanation=explanation,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))