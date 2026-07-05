"""
Day 16: Measure actual batch processing time.
Run this once to get real numbers for your resume bullet.
Usage: python measure_timing.py
"""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "app" / "scoring"))
sys.path.insert(0, str(Path(__file__).parent / "app" / "parsing"))

from parse_jd import parse_job_description
from parse_resume import parse_resume
from composite_score import compute_composite_score
from semantic_similarity import semantic_similarity_score

# Sample JD
JD_TEXT = """
Backend Engineer, 2-4 years experience.
Requirements: Python, FastAPI, PostgreSQL, Redis, Docker,
Kubernetes, AWS, REST API design, microservices.
Bonus: Celery, CI/CD pipelines.
"""

# Generate N sample resumes for timing
def make_resume(i):
    return f"""
    Skills: Python, FastAPI, PostgreSQL, Docker, AWS, Redis, REST API, Git.
    Experience: Backend Intern at Company{i} June 2024 - August 2024.
    Built REST APIs using Python and FastAPI. Optimized PostgreSQL queries.
    Deployed on AWS using Docker.
    """

def score_one(resume_text, jd_data):
    resume_data = parse_resume(resume_text)
    sem_result = semantic_similarity_score(resume_data, jd_data)
    score_data = compute_composite_score(resume_data, jd_data, sem_result["semantic_score"])
    return score_data["composite_score"]

if __name__ == "__main__":
    print("Loading model...")
    jd_data = parse_job_description(JD_TEXT)

    for n in [1, 5, 10, 20]:
        resumes = [make_resume(i) for i in range(n)]

        start = time.time()
        scores = [score_one(r, jd_data) for r in resumes]
        elapsed = time.time() - start

        print(f"{n:>3} resumes → {elapsed:.2f}s "
              f"({elapsed/n:.2f}s per resume) "
              f"| scores: {[round(s,1) for s in scores[:3]]}{'...' if n > 3 else ''}")