"""
Recruiter Analytics endpoint.

GET /analytics
  - Returns aggregated stats across all recruiter's JDs
  - Total candidates, avg score, top candidates
  - Skill distribution (most common matched/missing skills)
  - Shortlisting funnel (shortlisted/pending/rejected counts)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import Counter
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.db import models
from app.api.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


class TopCandidate(BaseModel):
    candidate_id: int
    composite_score: float
    jd_id: int
    status: Optional[str] = "pending"
    candidate_summary: Optional[str] = None


class AnalyticsResponse(BaseModel):
    total_jds: int
    total_candidates: int
    avg_composite_score: float
    top_score: float
    shortlisted_count: int
    rejected_count: int
    pending_count: int
    top_candidates: list[TopCandidate]
    most_common_matched_skills: list[dict]
    most_common_missing_skills: list[dict]
    score_distribution: dict


@router.get("", response_model=AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Get all JDs owned by this recruiter
    jds = db.query(models.JobDescription).filter(
        models.JobDescription.owner_id == current_user.id,
        models.JobDescription.id != 1  # exclude placeholder
    ).all()

    jd_ids = [jd.id for jd in jds]

    if not jd_ids:
        return AnalyticsResponse(
            total_jds=0, total_candidates=0,
            avg_composite_score=0, top_score=0,
            shortlisted_count=0, rejected_count=0, pending_count=0,
            top_candidates=[], most_common_matched_skills=[],
            most_common_missing_skills=[], score_distribution={}
        )

    # Get all candidates for these JDs
    candidates = db.query(models.Candidate).filter(
        models.Candidate.jd_id.in_(jd_ids)
    ).all()

    if not candidates:
        return AnalyticsResponse(
            total_jds=len(jds), total_candidates=0,
            avg_composite_score=0, top_score=0,
            shortlisted_count=0, rejected_count=0, pending_count=0,
            top_candidates=[], most_common_matched_skills=[],
            most_common_missing_skills=[], score_distribution={}
        )

    # Collect scores
    scores = []
    matched_skills_all = []
    missing_skills_all = []
    status_counts = Counter()
    top_candidates_data = []

    for candidate in candidates:
        score = candidate.score
        if not score:
            continue

        scores.append(score.composite_score)
        matched_skills_all.extend(score.matched_skills or [])
        missing_skills_all.extend(score.missing_skills or [])
        status_counts[candidate.status or "pending"] += 1

        summary = None
        if score.explanation:
            summary = score.explanation.candidate_summary

        top_candidates_data.append({
            "candidate_id": candidate.id,
            "composite_score": score.composite_score,
            "jd_id": candidate.jd_id,
            "status": candidate.status or "pending",
            "candidate_summary": summary,
        })

    if not scores:
        return AnalyticsResponse(
            total_jds=len(jds), total_candidates=len(candidates),
            avg_composite_score=0, top_score=0,
            shortlisted_count=0, rejected_count=0, pending_count=0,
            top_candidates=[], most_common_matched_skills=[],
            most_common_missing_skills=[], score_distribution={}
        )

    # Top 5 candidates by score
    top_candidates_data.sort(key=lambda x: x["composite_score"], reverse=True)
    top_5 = top_candidates_data[:5]

    # Skill frequency
    matched_counter = Counter(matched_skills_all).most_common(8)
    missing_counter = Counter(missing_skills_all).most_common(8)

    # Score distribution buckets
    score_dist = {"0-25": 0, "25-50": 0, "50-75": 0, "75-100": 0}
    for s in scores:
        if s < 25: score_dist["0-25"] += 1
        elif s < 50: score_dist["25-50"] += 1
        elif s < 75: score_dist["50-75"] += 1
        else: score_dist["75-100"] += 1

    return AnalyticsResponse(
        total_jds=len(jds),
        total_candidates=len(scores),
        avg_composite_score=round(sum(scores) / len(scores), 1),
        top_score=round(max(scores), 1),
        shortlisted_count=status_counts.get("shortlisted", 0),
        rejected_count=status_counts.get("rejected", 0),
        pending_count=status_counts.get("pending", 0),
        top_candidates=[TopCandidate(**c) for c in top_5],
        most_common_matched_skills=[{"skill": s, "count": c} for s, c in matched_counter],
        most_common_missing_skills=[{"skill": s, "count": c} for s, c in missing_counter],
        score_distribution=score_dist,
    )