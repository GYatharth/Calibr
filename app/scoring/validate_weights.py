"""
Day 8: Weights validation against a manually labeled gold set.

This is NOT a product feature — it's an engineering validation step.
The goal is to check whether the composite formula's rankings agree
with human judgment on a small set of labeled examples.

Why this matters:
- The weights (0.45 / 0.35 / 0.20) are a starting hypothesis
- This check turns "I made a formula" into "I validated my formula
  against labeled examples and here's what I found"
- Even a small gold set (5-20 examples) is enough to catch grossly
  wrong weights — and the story of what you found and adjusted is
  more valuable in an interview than a perfect-sounding formula

Usage: python app/scoring/validate_weights.py
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))

from skill_match import skill_match_score
from experience_score import experience_relevance_score
from composite_score import compute_composite_score, load_weights
from parse_jd import parse_job_description
from semantic_similarity import semantic_similarity_score


# ── JD we're validating against ──────────────────────────────────────────────
SAMPLE_JD = """
Backend Engineer, 2-4 years experience.
Requirements:
- Python and FastAPI or Django
- PostgreSQL and Redis
- Docker and Kubernetes
- AWS deployment experience
- REST API design and microservices
- Bonus: Celery, CI/CD pipelines
"""

# ── Gold set: 5 fictional candidates ─────────────────────────────────────────
# Each has: a name, skills list, experience entries, and your manual label.
# Fill in YOUR manual label (good/medium/poor) before running —
# that's the whole point: label first, run second, compare third.

GOLD_SET = [
    {
        "name": "Candidate A — Strong all-round fit",
        "manual_label": "good",  # your judgment: good/medium/poor
        "resume_data": {
            "skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker",
                       "Kubernetes", "AWS", "REST API", "CI/CD", "Celery"],
            "experience": [
                {
                    "title_line": "Backend Engineer, Flipkart",
                    "start_date": "2022-06-01T00:00:00",
                    "end_date": "2024-06-01T00:00:00",
                    "duration_months": 24,
                    "bullets": [
                        "Built REST APIs using Python and FastAPI",
                        "Managed PostgreSQL and Redis caching layer",
                        "Deployed services on AWS using Docker and Kubernetes",
                    ],
                }
            ],
            "education": [],
            "total_experience_months": 24,
        },
    },
    {
        "name": "Candidate B — Right skills, short experience",
        "manual_label": "medium",
        "resume_data": {
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "REST API"],
            "experience": [
                {
                    "title_line": "Backend Intern, Razorpay",
                    "start_date": "2024-01-01T00:00:00",
                    "end_date": "2024-06-01T00:00:00",
                    "duration_months": 5,
                    "bullets": [
                        "Built REST APIs with FastAPI and PostgreSQL",
                        "Deployed on AWS using Docker",
                    ],
                }
            ],
            "education": [],
            "total_experience_months": 5,
        },
    },
    {
        "name": "Candidate C — Wrong tech stack, good experience",
        "manual_label": "poor",
        "resume_data": {
            "skills": ["Java", "Spring Boot", "MySQL", "Angular", "Azure"],
            "experience": [
                {
                    "title_line": "Software Engineer, Infosys",
                    "start_date": "2021-01-01T00:00:00",
                    "end_date": "2024-01-01T00:00:00",
                    "duration_months": 36,
                    "bullets": [
                        "Built enterprise apps using Java and Spring Boot",
                        "Worked with MySQL and Angular frontend",
                    ],
                }
            ],
            "education": [],
            "total_experience_months": 36,
        },
    },
    {
        "name": "Candidate D — Partial match, some relevant skills",
        "manual_label": "medium",
        "resume_data": {
            "skills": ["Python", "Flask", "PostgreSQL", "Docker", "REST API"],
            "experience": [
                {
                    "title_line": "Junior Developer, Startup",
                    "start_date": "2023-01-01T00:00:00",
                    "end_date": "2024-06-01T00:00:00",
                    "duration_months": 17,
                    "bullets": [
                        "Built REST APIs using Python and Flask",
                        "Used PostgreSQL for data storage",
                        "Containerized services with Docker",
                    ],
                }
            ],
            "education": [],
            "total_experience_months": 17,
        },
    },
    {
        "name": "Candidate E — No relevant skills or experience",
        "manual_label": "poor",
        "resume_data": {
            "skills": ["HTML", "CSS", "JavaScript", "React"],
            "experience": [
                {
                    "title_line": "Frontend Intern, Agency",
                    "start_date": "2024-01-01T00:00:00",
                    "end_date": "2024-03-01T00:00:00",
                    "duration_months": 2,
                    "bullets": [
                        "Built landing pages using HTML, CSS, React",
                    ],
                }
            ],
            "education": [],
            "total_experience_months": 2,
        },
    },
]


def run_validation():
    jd_data = parse_job_description(SAMPLE_JD)
    results = []

    print("[info] Loading model for semantic similarity...")
    print()

    for candidate in GOLD_SET:
        # Semantic similarity needs actual text, so we build it
        # from the structured resume data
        skills_text = "Skills: " + ", ".join(candidate["resume_data"]["skills"])
        bullets_text = " ".join(
            b
            for exp in candidate["resume_data"]["experience"]
            for b in exp.get("bullets", [])
        )
        resume_text_for_embedding = skills_text + " " + bullets_text

        # Build a minimal resume_data-like dict for semantic scoring
        sem_result = semantic_similarity_score(
            candidate["resume_data"], jd_data
        )

        score = compute_composite_score(
            candidate["resume_data"],
            jd_data,
            sem_result["semantic_score"],
        )

        results.append({
            "name": candidate["name"],
            "manual_label": candidate["manual_label"],
            "composite_score": score["composite_score"],
            "skill_score": score["skill_score"],
            "semantic_score": score["semantic_score"],
            "experience_score": score["experience_score"],
        })

    # Sort by composite score descending (formula's ranking)
    results.sort(key=lambda x: x["composite_score"], reverse=True)

    print("=" * 70)
    print("VALIDATION RESULTS — formula ranking vs your manual labels")
    print("=" * 70)
    print(f"{'Rank':<5} {'Candidate':<45} {'Score':<8} {'Your Label'}")
    print("-" * 70)
    for i, r in enumerate(results, 1):
        name_short = r["name"][:44]
        print(f"{i:<5} {name_short:<45} {r['composite_score']:<8} {r['manual_label']}")

    print()
    print("Signal breakdown:")
    print(f"{'Candidate':<45} {'Skill':>7} {'Semantic':>10} {'Exp':>7} {'Total':>7}")
    print("-" * 70)
    for r in results:
        print(f"{r['name'][:44]:<45} {r['skill_score']:>7.1f} {r['semantic_score']:>10.1f} {r['experience_score']:>7.1f} {r['composite_score']:>7.1f}")

    print()
    print("─" * 70)
    print("WHAT TO CHECK:")
    print("  ✓ Do all 'good' labels rank above 'medium' labels?")
    print("  ✓ Do all 'medium' labels rank above 'poor' labels?")
    print("  ✓ If not — which signal is causing the disagreement?")
    print("  ✓ Write your findings in validation_notes.md")
    print("─" * 70)


if __name__ == "__main__":
    run_validation()