"""
Day 4: Skill-graph matching.

First of the three scoring signals. Compares candidate skills (from
parse_resume.py) against JD required skills (from parse_jd.py) using
the same taxonomy both modules already share.

Output:
  - match_pct: percentage of JD required skills the candidate has (0-100)
  - matched_skills: canonical skill names found in both
  - missing_skills: canonical skill names required but not found
  - skill_match_score: normalized 0-100 score (same as match_pct for now,
    kept as a named field so the composite formula has a clean interface)

This is intentionally the simplest of the three signals — it catches
explicit hard requirements precisely. Its blind spot (paraphrased
experience, soft equivalencies) is covered by the semantic similarity
signal on Day 5.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))
from parse_jd import parse_job_description
from parse_resume import parse_resume
from extract_pdf import extract_resume_text


def skill_match_score(
    candidate_skills: list[str],
    required_skills: list[str],
) -> dict:
    """
    Computes skill-graph match between a candidate and a JD.

    Args:
        candidate_skills: canonical skill names from parse_resume()
        required_skills:  canonical skill names from parse_job_description()

    Returns a dict with:
        skill_match_score (float 0-100)
        matched_skills    (list)
        missing_skills    (list)
        match_pct         (float, same value — explicit for readability)
    """
    if not required_skills:
        # If the JD specified no recognizable required skills, we can't
        # score this signal — return neutral 50 rather than 0 or 100,
        # and flag it so the composite formula can handle it.
        return {
            "skill_match_score": 50.0,
            "matched_skills": [],
            "missing_skills": [],
            "match_pct": 50.0,
            "note": "No required skills detected in JD — skill match signal is neutral",
        }

    candidate_set = set(candidate_skills)
    required_set = set(required_skills)

    matched = sorted(candidate_set & required_set)
    missing = sorted(required_set - candidate_set)

    match_pct = round((len(matched) / len(required_set)) * 100, 2)

    return {
        "skill_match_score": match_pct,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_pct": match_pct,
    }


if __name__ == "__main__":
    # Day 4 task: run skill matching against the sample resume and JD,
    # print the full result so we can visually verify correctness.
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

    # Parse JD
    jd_data = parse_job_description(sample_jd)

    # Parse resume
    raw_text = extract_resume_text("sample_data/sample_resume.pdf")
    resume_data = parse_resume(raw_text)

    # Score
    result = skill_match_score(
        candidate_skills=resume_data["skills"],
        required_skills=jd_data["required_skills"],
    )

    print("=" * 60)
    print("Skill-graph match result")
    print("=" * 60)
    print(f"JD required skills  : {jd_data['required_skills']}")
    print(f"Candidate skills    : {resume_data['skills']}")
    print()
    print(json.dumps(result, indent=2))