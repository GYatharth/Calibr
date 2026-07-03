"""
Day 13: Single-resume scoring endpoint (updated).

Changes from Day 11:
- Accepts jd_id instead of jd_text (JD now uploaded separately via /jd)
- Auth required — scoped to current user
- Ownership check on JD before scoring
- Removes hardcoded jd_id=1 placeholder
"""

import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent / "scoring"))
sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))

from app.api.schemas import SingleScoreRequest, ScoreResponse, SignalBreakdown
from app.api.auth import get_current_user
from app.db.database import get_db
from app.db import models

from parse_jd import parse_job_description
from parse_resume import parse_resume
from composite_score import compute_composite_score
from explainer import generate_explanation
from semantic_similarity import semantic_similarity_score

router = APIRouter(prefix="/score", tags=["scoring"])


@router.post("", response_model=ScoreResponse)
def score_resume(
    request: SingleScoreRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Score one resume against one job description.

    Full pipeline:
    1. Verify JD exists and belongs to current user (ownership check)
    2. Parse JD from DB + parse resume text
    3. Compute all three signals
    4. Combine into weighted composite score
    5. Generate LLM explanation
    6. Persist candidate + score + explanation to PostgreSQL
    7. Return full ScoreResponse
    """
    try:
        # Step 1: ownership check — IDOR prevention
        jd = db.query(models.JobDescription).filter(
            models.JobDescription.id == request.jd_id,
            models.JobDescription.owner_id == current_user.id,
        ).first()
        if not jd:
            raise HTTPException(
                status_code=404,
                detail="JD not found or not authorised"
            )

        # Step 2: parse
        jd_data = parse_job_description(jd.raw_text)
        resume_data = parse_resume(request.resume_text)

        # Step 3-5: score + explain
        sem_result = semantic_similarity_score(resume_data, jd_data)
        score_data = compute_composite_score(
            resume_data, jd_data, sem_result["semantic_score"]
        )
        explanation = generate_explanation(score_data, jd_data)

        # Step 6: persist to DB
        candidate = models.Candidate(
            jd_id=request.jd_id,
            raw_resume_text=request.resume_text,
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
            missing_skills=score_data["missing_skills"],
        )
        db.add(exp_record)
        db.commit()

        # Step 7: return response
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
        raise  # re-raise HTTP exceptions as-is
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))