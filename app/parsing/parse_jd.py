"""
Day 2: Job description parsing.

JDs are short and structured enough that regex + taxonomy lookup is
sufficient — no need for heavier NLP here. This keeps JD parsing fast
and easy to explain in interviews: "I match JD text against a
hand-curated skill taxonomy with synonym resolution."

This module also does light extraction of required years of experience,
since that feeds the experience-relevance signal later (Day 6).
"""

import json
import re
from pathlib import Path

TAXONOMY_PATH = Path(__file__).parent.parent / "data" / "skills_taxonomy.json"


def load_taxonomy() -> dict:
    """Loads the skill taxonomy and builds a reverse lookup:
    alias (lowercase) -> canonical skill name."""
    with open(TAXONOMY_PATH) as f:
        raw = json.load(f)

    alias_to_canonical = {}
    for canonical, aliases in raw.items():
        if canonical.startswith("_"):
            continue  # skip the _comment field
        # the canonical name itself should also match
        alias_to_canonical[canonical.lower()] = canonical
        for alias in aliases:
            alias_to_canonical[alias.lower()] = canonical

    return alias_to_canonical


def extract_skills_from_text(text: str, alias_lookup: dict) -> list[str]:
    """
    Scans free text for any known skill alias and returns the set of
    canonical skill names found. Uses word-boundary matching so "Go"
    doesn't match inside "Google", and sorts aliases longest-first so
    "Spring Boot" matches before the shorter "Spring".
    """
    text_lower = text.lower()
    found = set()

    # Sort longest-first to prefer more specific matches
    # (e.g. match "spring boot" before the standalone "spring" alias).
    sorted_aliases = sorted(alias_lookup.keys(), key=len, reverse=True)

    for alias in sorted_aliases:
        # Escape regex special chars (e.g. "C++", "Node.js")
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(alias) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found.add(alias_lookup[alias])

    return sorted(found)


def extract_required_experience_years(jd_text: str) -> int | None:
    """
    Pulls a 'minimum years of experience' number out of JD text if
    present, e.g. '3+ years of experience' or '2-4 years experience'.
    Returns None if no such pattern is found — not every JD states this.
    """
    patterns = [
        r"(\d+)\+?\s*(?:-|to)\s*\d+\s*years?",  # "2-4 years" -> take lower bound
        r"(\d+)\+?\s*years?\s*(?:of)?\s*experience",
        r"minimum\s*(?:of)?\s*(\d+)\s*years?",
    ]
    for pattern in patterns:
        match = re.search(pattern, jd_text.lower())
        if match:
            return int(match.group(1))
    return None


def parse_job_description(jd_text: str) -> dict:
    """
    Main entry point for Day 2. Takes raw JD text, returns a structured
    dict: required skills (canonical names) and required experience years.
    """
    alias_lookup = load_taxonomy()
    required_skills = extract_skills_from_text(jd_text, alias_lookup)
    required_experience_years = extract_required_experience_years(jd_text)

    return {
        "required_skills": required_skills,
        "required_experience_years": required_experience_years,
        "raw_text": jd_text.strip(),
    }


if __name__ == "__main__":
    # Day 2 task: parse a sample JD and print the extracted structured data.
    sample_jd = """
    We are hiring a Backend Engineer with 2-4 years of experience.

    Requirements:
    - Strong proficiency in Python and experience with FastAPI or Django
    - Hands-on experience with PostgreSQL and Redis
    - Familiarity with Docker and basic Kubernetes (k8s) concepts
    - Experience deploying on AWS
    - Understanding of REST API design and microservices architecture
    - Bonus: experience with Celery for async task processing

    Nice to have:
    - Exposure to machine learning or NLP projects
    - Familiarity with CI/CD pipelines
    """

    result = parse_job_description(sample_jd)
    print("=" * 60)
    print("Parsed job description")
    print("=" * 60)
    print(f"Required experience: {result['required_experience_years']} years")
    print(f"Required skills found ({len(result['required_skills'])}):")
    for skill in result["required_skills"]:
        print(f"  - {skill}")