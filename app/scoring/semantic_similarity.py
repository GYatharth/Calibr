"""
Day 5: Semantic similarity scoring.

Second of the three scoring signals. Uses sentence-transformers to
generate dense vector embeddings of resume text and JD text, then
computes cosine similarity between them.

Why this signal exists alongside skill matching:
- Skill matching catches explicit requirements precisely
- Semantic similarity catches paraphrased/equivalent experience that
  exact matching misses (e.g. "led a team" vs "managed engineers",
  or a candidate who wrote "built distributed systems" when the JD
  says "microservices architecture")

Model choice: all-MiniLM-L6-v2
- Small (80MB), fast, runs fully locally — no API cost per resume
- Strong performance on semantic textual similarity benchmarks
- First run will download the model (~80MB); subsequent runs use cache
"""

import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))
from parse_jd import parse_job_description
from parse_resume import parse_resume
from extract_pdf import extract_resume_text

# Load model once at module level — expensive to reload per call.
# First run downloads ~80MB to ~/.cache/huggingface/
print("[info] Loading sentence-transformer model (first run downloads ~80MB)...")
MODEL = SentenceTransformer("all-MiniLM-L6-v2")
print("[info] Model loaded.")


def build_resume_text_for_embedding(resume_data: dict) -> str:
    """
    Constructs a clean, flat text representation of the resume for
    embedding — combining skills, experience bullets, and education
    into one string. We embed meaning, not raw PDF text, so structured
    content is more signal-dense than raw text with headers/formatting.
    """
    parts = []

    # Skills
    if resume_data.get("skills"):
        parts.append("Skills: " + ", ".join(resume_data["skills"]))

    # Experience bullets
    for exp in resume_data.get("experience", []):
        parts.append(exp.get("title_line", ""))
        for bullet in exp.get("bullets", []):
            parts.append(bullet)

    # Education
    for edu in resume_data.get("education", []):
        parts.append(edu.get("raw_text", ""))

    return " ".join(parts)


def build_jd_text_for_embedding(jd_data: dict) -> str:
    """
    Constructs a clean text representation of the JD for embedding.
    Uses required skills + raw JD text combined for maximum signal.
    """
    parts = []

    if jd_data.get("required_skills"):
        parts.append("Required skills: " + ", ".join(jd_data["required_skills"]))

    if jd_data.get("raw_text"):
        parts.append(jd_data["raw_text"])

    return " ".join(parts)


def semantic_similarity_score(
    resume_data: dict,
    jd_data: dict,
) -> dict:
    """
    Computes semantic similarity between a resume and a JD.

    Args:
        resume_data: structured dict from parse_resume()
        jd_data:     structured dict from parse_job_description()

    Returns a dict with:
        semantic_score (float 0-100)
        raw_cosine     (float 0-1, the actual cosine similarity value)
    """
    resume_text = build_resume_text_for_embedding(resume_data)
    jd_text = build_jd_text_for_embedding(jd_data)

    # Generate embeddings — returns a tensor per text
    resume_embedding = MODEL.encode(resume_text, convert_to_tensor=True)
    jd_embedding = MODEL.encode(jd_text, convert_to_tensor=True)

    # Cosine similarity returns a value between -1 and 1.
    # In practice for these texts it'll be between 0 and 1.
    # We scale to 0-100 for consistency with the other two signals.
    cosine_sim = util.cos_sim(resume_embedding, jd_embedding).item()
    score = round(max(0.0, cosine_sim) * 100, 2)

    return {
        "semantic_score": score,
        "raw_cosine": round(cosine_sim, 4),
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

    result = semantic_similarity_score(resume_data, jd_data)

    print("=" * 60)
    print("Semantic similarity result")
    print("=" * 60)
    print(f"Resume text (for embedding): {build_resume_text_for_embedding(resume_data)[:120]}...")
    print()
    print(json.dumps(result, indent=2))