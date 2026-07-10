"""
Semantic similarity scoring — TF-IDF version for deployment.

Uses TF-IDF cosine similarity instead of sentence-transformers.
Much lighter memory footprint (~10MB vs ~400MB) — runs on free hosting.

Trade-off: slightly less accurate than neural embeddings for paraphrased
text, but still captures keyword-level semantic overlap well.

Interview answer: "The local version uses sentence-transformers neural
embeddings. The deployed version uses TF-IDF cosine similarity for
memory efficiency on free hosting — same architecture, different
similarity backend."
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))


def build_resume_text_for_embedding(resume_data: dict) -> str:
    """Builds flat text representation of resume for TF-IDF."""
    parts = []
    if resume_data.get("skills"):
        parts.append("Skills: " + ", ".join(resume_data["skills"]))
    for exp in resume_data.get("experience", []):
        parts.append(exp.get("title_line", ""))
        for bullet in exp.get("bullets", []):
            parts.append(bullet)
    for edu in resume_data.get("education", []):
        parts.append(edu.get("raw_text", ""))
    return " ".join(parts)


def build_jd_text_for_embedding(jd_data: dict) -> str:
    """Builds flat text representation of JD for TF-IDF."""
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
    Computes TF-IDF cosine similarity between resume and JD.
    Returns same interface as the sentence-transformers version
    so nothing else in the codebase needs to change.
    """
    resume_text = build_resume_text_for_embedding(resume_data)
    jd_text = build_jd_text_for_embedding(jd_data)

    if not resume_text.strip() or not jd_text.strip():
        return {"semantic_score": 0.0, "raw_cosine": 0.0}

    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),  # unigrams + bigrams for better coverage
        max_features=5000,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
        cosine_sim = cosine_similarity(
            tfidf_matrix[0:1], tfidf_matrix[1:2]
        )[0][0]
        score = round(float(cosine_sim) * 100, 2)
    except Exception:
        score = 0.0
        cosine_sim = 0.0

    return {
        "semantic_score": score,
        "raw_cosine": round(float(cosine_sim), 4),
    }


if __name__ == "__main__":
    # Quick test
    from parse_jd import parse_job_description
    from parse_resume import parse_resume

    sample_jd = """
    Backend Engineer, 2-4 years experience.
    Requirements: Python, FastAPI, PostgreSQL, Redis, Docker, AWS.
    """
    sample_resume = """
    Skills: Python, FastAPI, PostgreSQL, Docker, AWS, Redis.
    Experience: Backend Engineer at Flipkart June 2022 - June 2024.
    Built REST APIs using Python and FastAPI.
    """

    jd_data = parse_job_description(sample_jd)
    resume_data = parse_resume(sample_resume)
    result = semantic_similarity_score(resume_data, jd_data)
    print(f"Semantic score: {result['semantic_score']}")
    print(f"Raw cosine: {result['raw_cosine']}")