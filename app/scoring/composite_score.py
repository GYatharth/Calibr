"""
Day 7: Weighted composite ATS score.

Combines the three signals into one final score using configurable
weights stored in config.json — not hardcoded here.

Formula:
  score = (w1 × skill_match) + (w2 × semantic_similarity) + (w3 × experience_relevance)

Starting weights: w1=0.45, w2=0.35, w3=0.20

Why these weights:
  - Skill match weighted highest (0.45): explicit JD requirements are
    the most direct signal of fit — if a JD says "must have AWS" that
    should carry more weight than a soft semantic match
  - Semantic similarity second (0.35): captures meaning/context that
    skill matching misses, but is less precise than explicit requirements
  - Experience weighting lowest (0.20): important but penalizes students
    and career-changers heavily — kept as a supporting signal, not dominant

These are a starting hypothesis, not ground truth. Day 8 validates
them against a labeled set and adjusts if needed.
"""

import json
import sys
from pathlib import Path

# Scoring signals
sys.path.insert(0, str(Path(__file__).parent))
from skill_match import skill_match_score
from experience_score import experience_relevance_score

sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))
from parse_jd import parse_job_description
from parse_resume import parse_resume
from extract_pdf import extract_resume_text

CONFIG_PATH = Path(__file__).parent.parent.parent / "config.json"


def load_weights() -> dict:
    """
    Loads scoring weights from config.json.
    Falls back to defaults if config is missing or malformed —
    so the system still works even if config gets corrupted.
    """
    defaults = {"w1_skill": 0.45, "w2_semantic": 0.35, "w3_experience": 0.20}
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        weights = config.get("scoring_weights", defaults)
        # Validate weights sum to ~1.0
        total = sum(weights.values())
        if not (0.99 <= total <= 1.01):
            print(f"[warn] Weights sum to {total:.2f}, not 1.0 — using defaults")
            return defaults
        return weights
    except (FileNotFoundError, json.JSONDecodeError):
        print("[warn] config.json not found or invalid — using default weights")
        return defaults


def compute_composite_score(
    resume_data: dict,
    jd_data: dict,
    semantic_score: float,
) -> dict:
    """
    Computes the weighted composite ATS score from all three signals.

    Args:
        resume_data:    structured dict from parse_resume()
        jd_data:        structured dict from parse_job_description()
        semantic_score: float 0-100 from semantic_similarity_score()
                        (passed in rather than recomputed — embedding
                        inference is expensive, don't run it twice)

    Returns a dict with:
        composite_score   (float 0-100)
        skill_score       (float 0-100)
        semantic_score    (float 0-100)
        experience_score  (float 0-100)
        weights_used      (dict)
        signal_breakdown  (dict — human-readable per-signal contribution)
        matched_skills    (list)
        missing_skills    (list)
        experience_gap    (str)
    """
    weights = load_weights()

    # Signal 1: skill match
    skill_result = skill_match_score(
        candidate_skills=resume_data["skills"],
        required_skills=jd_data["required_skills"],
    )

    # Signal 2: semantic similarity (passed in, not recomputed)
    s2 = semantic_score

    # Signal 3: experience relevance
    exp_result = experience_relevance_score(resume_data, jd_data)

    s1 = skill_result["skill_match_score"]
    s3 = exp_result["experience_score"]

    w1 = weights["w1_skill"]
    w2 = weights["w2_semantic"]
    w3 = weights["w3_experience"]

    composite = round((w1 * s1) + (w2 * s2) + (w3 * s3), 2)

    return {
        "composite_score": composite,
        "skill_score": s1,
        "semantic_score": s2,
        "experience_score": s3,
        "weights_used": weights,
        "signal_breakdown": {
            "skill_contribution":      round(w1 * s1, 2),
            "semantic_contribution":   round(w2 * s2, 2),
            "experience_contribution": round(w3 * s3, 2),
        },
        "matched_skills": skill_result["matched_skills"],
        "missing_skills": skill_result["missing_skills"],
        "experience_gap": exp_result["experience_gap"],
        "experience_entries": exp_result["entry_scores"],
    }


if __name__ == "__main__":
    # Lazy import here to avoid loading the model at module level
    # when composite_score is imported by other modules
    from semantic_similarity import semantic_similarity_score

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

    sem_result = semantic_similarity_score(resume_data, jd_data)
    result = compute_composite_score(resume_data, jd_data, sem_result["semantic_score"])

    print("=" * 60)
    print("Composite ATS Score")
    print("=" * 60)
    print(f"  Skill match score    : {result['skill_score']} × {result['weights_used']['w1_skill']} = {result['signal_breakdown']['skill_contribution']}")
    print(f"  Semantic score       : {result['semantic_score']} × {result['weights_used']['w2_semantic']} = {result['signal_breakdown']['semantic_contribution']}")
    print(f"  Experience score     : {result['experience_score']} × {result['weights_used']['w3_experience']} = {result['signal_breakdown']['experience_contribution']}")
    print(f"  {'─' * 40}")
    print(f"  COMPOSITE SCORE      : {result['composite_score']} / 100")
    print()
    print(f"  Matched skills  : {result['matched_skills']}")
    print(f"  Missing skills  : {result['missing_skills']}")
    print(f"  Experience gap  : {result['experience_gap']}")