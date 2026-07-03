"""
Day 11: Single-resume scoring endpoint.

POST /score
  - Accepts: JD text + resume text
  - Runs: full scoring pipeline (skill match + semantic + experience + LLM explanation)
  - Stores: candidate + score + explanation in PostgreSQL
  - Returns: full ScoreResponse

This is the core endpoint of Calibr. Everything built in Phase 2
(Days 4-9) gets called from here in the right order.
"""

import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Add scoring and parsing modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scoring"))
sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))

from app.api.schemas import SingleScoreRequest, ScoreResponse, SignalBreakdown
from app.db.database import get_db
from app.db import models

from parse_jd import parse_job_description
from parse_resume import parse_resume
from skill_match import skill_match_score
from experience_score import experience_relevance_score
from composite_score import compute_composite_score
from explainer import generate_explanation

# Lazy import semantic similarity to avoid reloading the model
# on every request — it's loaded once at module level in semantic_similarity.py
from semantic_similarity import semantic_similarity_score

router = APIRouter(prefix="/score", tags=["scoring"])


@router.post("", response_model=ScoreResponse)
def score_resume(request: SingleScoreRequest, db: Session = Depends(get_db)):
    """
    Score one resume against one job description.

    Full pipeline:
    1. Parse JD text → required skills, experience requirement
    2. Parse resume text → candidate skills, experience entries
    3. Compute skill match score (signal 1)
    4. Compute semantic similarity score (signal 2)
    5. Compute experience relevance score (signal 3)
    6. Combine into weighted composite score
    7. Generate LLM explanation (Groq)
    8. Persist candidate + score + explanation to PostgreSQL
    9. Return full ScoreResponse
    """
    try:
        # Step 1 & 2: parse
        jd_data = parse_job_description(request.jd_text)
        resume_data = parse_resume(request.resume_text)

        # Step 3-6: score
        sem_result = semantic_similarity_score(resume_data, jd_data)
        score_data = compute_composite_score(
            resume_data, jd_data, sem_result["semantic_score"]
        )

        # Step 7: explain
        explanation = generate_explanation(score_data, jd_data)

        # Step 8: persist to DB
        # Store candidate
        candidate = models.Candidate(
            jd_id=1,  # placeholder until JD upload endpoint exists (Day 12)
            raw_resume_text=request.resume_text,
            extracted_skills=resume_data["skills"],
            extracted_experience=resume_data["experience"],
            total_experience_months=resume_data["total_experience_months"],
        )
        db.add(candidate)
        db.flush()  # get candidate.id without committing

        # Store score
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

        # Store explanation
        exp_record = models.Explanation(
            score_id=score.id,
            explanation_text=explanation,
            missing_skills=score_data["missing_skills"],
        )
        db.add(exp_record)
        db.commit()

        # Step 9: return response
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

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))