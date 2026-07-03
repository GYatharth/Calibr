"""
Day 6: Experience-relevance weighting.

Third and final scoring signal. Weights a candidate's experience by
two factors:
  1. Recency — experience from the last 2 years scores higher than
     experience from 5 years ago
  2. Duration — longer sustained experience scores higher than a
     brief one-off mention

Why this signal exists:
- Skill matching catches whether a skill is present at all
- Semantic similarity catches meaning/context
- But neither distinguishes between someone who used Python daily
  for 3 years vs someone who mentioned Python once in a side project
  in 2019. That's what this signal fixes.

Output: a normalized 0-100 score reflecting how recent and sustained
the candidate's experience is relative to what the JD requires.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))
from parse_jd import parse_job_description
from parse_resume import parse_resume
from extract_pdf import extract_resume_text


def recency_weight(end_date_iso: str, as_of: datetime = None) -> float:
    """
    Returns a recency multiplier (0.0 to 1.0) based on how recently
    the experience ended.

    Decay schedule:
      - Ended within last 12 months  → 1.0  (full weight)
      - Ended 1-2 years ago          → 0.8
      - Ended 2-3 years ago          → 0.6
      - Ended 3-5 years ago          → 0.4
      - Ended 5+ years ago           → 0.2  (still counts, just stale)

    This is a deliberate, tunable design decision — document it in
    your README and be ready to defend it in interviews.
    """
    if as_of is None:
        as_of = datetime.now()

    end_date = datetime.fromisoformat(end_date_iso)
    years_ago = (as_of - end_date).days / 365.25

    if years_ago <= 1:
        return 1.0
    elif years_ago <= 2:
        return 0.8
    elif years_ago <= 3:
        return 0.6
    elif years_ago <= 5:
        return 0.4
    else:
        return 0.2


def duration_score(duration_months: int) -> float:
    """
    Returns a duration score (0.0 to 1.0) based on how long the
    candidate held a role.

    Scale:
      - 12+ months  → 1.0  (substantial, sustained experience)
      - 6-11 months → 0.7
      - 3-5 months  → 0.5  (internship-length, meaningful but shorter)
      - 1-2 months  → 0.3
      - < 1 month   → 0.1
    """
    if duration_months >= 12:
        return 1.0
    elif duration_months >= 6:
        return 0.7
    elif duration_months >= 3:
        return 0.5
    elif duration_months >= 1:
        return 0.3
    else:
        return 0.1


def experience_relevance_score(
    resume_data: dict,
    jd_data: dict,
) -> dict:
    """
    Computes an experience-relevance score by combining:
    - How recent each role was (recency weight)
    - How long the candidate held each role (duration score)
    - Whether the role's skills overlap with JD requirements
      (relevance multiplier)

    Each experience entry contributes a weighted score. The final
    score is normalized to 0-100.

    Args:
        resume_data: structured dict from parse_resume()
        jd_data:     structured dict from parse_job_description()

    Returns a dict with:
        experience_score (float 0-100)
        entry_scores     (list of per-role score breakdowns)
        total_experience_months (int)
        required_experience_years (int or None)
        experience_gap (str — simple flag for the LLM explanation layer)
    """
    required_skills = set(jd_data.get("required_skills", []))
    experience_entries = resume_data.get("experience", [])
    total_months = resume_data.get("total_experience_months", 0)
    required_years = jd_data.get("required_experience_years")

    if not experience_entries:
        return {
            "experience_score": 0.0,
            "entry_scores": [],
            "total_experience_months": 0,
            "required_experience_years": required_years,
            "experience_gap": "no_experience_found",
        }

    entry_scores = []
    weighted_scores = []

    for entry in experience_entries:
        # Recency: how recently did this role end?
        recency = recency_weight(entry["end_date"])

        # Duration: how long was this role?
        duration = duration_score(entry["duration_months"])

        # Relevance: do the skills mentioned in this role's bullets
        # overlap with what the JD requires?
        # We do a simple keyword scan of the bullet text against
        # required skill names — rough but fast and explainable.
        bullet_text = " ".join(entry.get("bullets", [])).lower()
        matched_required = [
            s for s in required_skills
            if s.lower() in bullet_text
        ]
        # Relevance multiplier: 1.0 if any required skills appear
        # in the bullets, 0.6 if not (role still counts, just less
        # directly relevant to this specific JD).
        relevance = 1.0 if matched_required else 0.6

        # Combined entry score (0-1 scale)
        entry_score = recency * duration * relevance

        entry_scores.append({
            "title_line": entry["title_line"],
            "duration_months": entry["duration_months"],
            "recency_weight": recency,
            "duration_score": duration,
            "relevance_multiplier": relevance,
            "matched_required_skills_in_bullets": matched_required,
            "entry_score": round(entry_score, 3),
        })
        weighted_scores.append(entry_score)

    # Final score: average of all entry scores, normalized to 0-100
    avg_score = sum(weighted_scores) / len(weighted_scores)
    final_score = round(avg_score * 100, 2)

    # Experience gap check vs JD requirement
    total_years = total_months / 12
    if required_years and total_years < required_years:
        gap = f"below_required ({total_years:.1f} yrs vs {required_years} required)"
    elif required_years and total_years >= required_years:
        gap = "meets_required"
    else:
        gap = "no_requirement_stated"

    return {
        "experience_score": final_score,
        "entry_scores": entry_scores,
        "total_experience_months": total_months,
        "required_experience_years": required_years,
        "experience_gap": gap,
    }


if __name__ == "__main__":
    import json

    sample_jd = """
    Backend Engineer, 2-4 years experience.

    Requirements:
    - Strong proficiency in Python and FastAPI or Django
    - Hands-on experience with PostgreSQL and Redis
    - Familiarity with Docker and Kubernetes (k8s)
    - Experience deploying on AWS
    - Understanding of REST API design and microservices
    - Bonus: Celery for async task processing, CI/CD pipelines
    """

    jd_data = parse_job_description(sample_jd)
    raw_text = extract_resume_text("sample_data/sample_resume.pdf")
    resume_data = parse_resume(raw_text)

    result = experience_relevance_score(resume_data, jd_data)

    print("=" * 60)
    print("Experience relevance result")
    print("=" * 60)
    print(json.dumps(result, indent=2))