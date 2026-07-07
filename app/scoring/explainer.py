"""
Day 9: LLM explanation layer.

This module receives an already-computed composite score and its
three signal values, and generates a natural-language explanation
using Groq's API.

Critical design boundary:
- The LLM receives the score as INPUT
- The LLM explains the score as OUTPUT
- The LLM never generates or modifies the score itself
- Application code never parses LLM output back into score fields

This boundary is enforced in two ways:
1. The prompt explicitly tells the LLM the score is already computed
2. The return value of this function is always a string (explanation),
   never a number — so it physically cannot overwrite a score field

This is the single design decision that most differentiates Calibr
from a typical LLM-wrapper resume screener.
"""

import os
import sys
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # reads GROQ_API_KEY from .env file

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))

from skill_match import skill_match_score
from experience_score import experience_relevance_score
from composite_score import compute_composite_score
from parse_jd import parse_job_description
from parse_resume import parse_resume
from extract_pdf import extract_resume_text


def build_explanation_prompt(score_data: dict, jd_data: dict) -> str:
    """
    Builds a tightly scoped prompt for the LLM.

    The prompt:
    1. Tells the LLM the score is already computed (not its job)
    2. Gives it only the signal values and skill lists it needs
    3. Asks for a structured explanation in plain English
    4. Explicitly forbids re-scoring or changing numbers
    """
    matched = ", ".join(score_data["matched_skills"]) or "none"
    missing = ", ".join(score_data["missing_skills"]) or "none"
    exp_gap = score_data["experience_gap"]
    required_skills = ", ".join(jd_data["required_skills"])

    prompt = f"""You are an assistant that explains pre-computed resume screening scores.
The score has already been calculated by the application. Your job is ONLY to explain
it in plain English. Do NOT suggest a different score or re-evaluate the candidate.

--- SCORE DATA (already computed, do not change) ---
Composite ATS Score : {score_data['composite_score']} / 100
Skill match score   : {score_data['skill_score']} / 100
Semantic score      : {score_data['semantic_score']} / 100
Experience score    : {score_data['experience_score']} / 100

--- SKILL ANALYSIS ---
JD required skills  : {required_skills}
Matched skills      : {matched}
Missing skills      : {missing}
Experience gap      : {exp_gap}

--- YOUR TASK ---
Write a 3-4 sentence plain-English explanation of this score for a recruiter.
Cover: (1) overall fit summary, (2) skill strengths, (3) what's missing,
(4) one specific suggestion for the candidate to improve their fit.
Be direct and specific. Do not use bullet points. Do not mention the word 'score'
more than once. Do not re-compute or question the numbers.
"""
    return prompt


def generate_explanation(score_data: dict, jd_data: dict) -> str:
    """
    Calls Groq API to generate a natural-language explanation of the
    pre-computed score. Returns a plain string — never a number,
    never parsed back into score fields.

    Args:
        score_data: output dict from compute_composite_score()
        jd_data:    output dict from parse_job_description()

    Returns:
        explanation_text (str)
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "[error] GROQ_API_KEY not found in environment. Check your .env file."

    client = Groq(api_key=api_key)
    prompt = build_explanation_prompt(score_data, jd_data)

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4,  # low temp = more consistent, less hallucination-prone
        )
        explanation = response.choices[0].message.content.strip()
        return explanation

    except Exception as e:
        return f"[error] Groq API call failed: {e}"

def generate_candidate_summary(score_data: dict, resume_data: dict) -> str:
    """
    Generates a one-sentence recruiter-facing candidate summary.
    Focuses on: experience level, strongest skills, key gaps.
    Much shorter than the full explanation — designed to appear
    inline in rankings without overwhelming the recruiter.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Summary unavailable."

    client = Groq(api_key=api_key)

    total_months = resume_data.get("total_experience_months", 0)
    years = round(total_months / 12, 1) if total_months else 0
    matched = ", ".join(score_data["matched_skills"][:5]) or "none"
    missing = ", ".join(score_data["missing_skills"][:3]) or "none"

    prompt = f"""Write a single sentence (max 20 words) summarizing this candidate for a recruiter.
Focus on: experience level, top matched skills, biggest gap.

Data:
- Experience: {years} years
- Matched skills: {matched}
- Missing skills: {missing}
- Composite score: {score_data['composite_score']}/100

Write ONLY the one sentence. No prefix, no punctuation at start, no explanation."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Score: {score_data['composite_score']}/100"


if __name__ == "__main__":
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
    score_data = compute_composite_score(
        resume_data, jd_data, sem_result["semantic_score"]
    )

    print("=" * 60)
    print("Composite ATS Score:", score_data["composite_score"], "/ 100")
    print("=" * 60)
    print()
    print("Generating explanation (Groq API)...")
    print()

    explanation = generate_explanation(score_data, jd_data)

    print("EXPLANATION:")
    print("-" * 60)
    print(explanation)
    print("-" * 60)
    print()
    print("Signal breakdown:")
    print(f"  Skill match  : {score_data['skill_score']}")
    print(f"  Semantic     : {score_data['semantic_score']}")
    print(f"  Experience   : {score_data['experience_score']}")
    print(f"  Missing      : {score_data['missing_skills']}")
    print(f"  Exp gap      : {score_data['experience_gap']}")