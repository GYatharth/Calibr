"""
Day 3: Resume structured extraction.

Converts raw resume text (from Day 1's PDF extractor) into structured
fields: skills, work experience entries (title, company, dates), and
education. Reuses the Day 2 skill taxonomy for skill matching so both
resumes and JDs are scored against the same canonical skill names.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_jd import load_taxonomy, extract_skills_from_text  # reuse Day 2 logic

_NLP = None
try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except (ImportError, OSError):
    _NLP = None


SECTION_HEADERS = {
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "education": ["education", "academic background"],
    "skills": ["skills", "technical skills", "skills & tools"],
    "projects": ["projects", "personal projects", "academic projects"],
    "certifications": ["certifications", "certificates"],
}

MONTHS = (
    "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    "january|february|march|april|june|july|august|september|october|november|december"
)


def split_into_sections(resume_text: str) -> dict[str, str]:
    lines = resume_text.split("\n")
    sections: dict[str, list[str]] = {"other": []}
    current_section = "other"

    for line in lines:
        stripped = line.strip()
        line_lower = stripped.lower()

        matched_section = None
        for section_name, headers in SECTION_HEADERS.items():
            if len(stripped.split()) <= 4 and any(
                line_lower == h or line_lower.startswith(h) for h in headers
            ):
                matched_section = section_name
                break

        if matched_section:
            current_section = matched_section
            sections.setdefault(current_section, [])
            continue

        sections.setdefault(current_section, [])
        sections[current_section].append(stripped)

    return {name: "\n".join(content).strip() for name, content in sections.items()}


def extract_skills(resume_text: str) -> list[str]:
    alias_lookup = load_taxonomy()
    return extract_skills_from_text(resume_text, alias_lookup)


def parse_date_range(text: str) -> tuple[datetime | None, datetime | None]:
    pattern = (
        rf"(?:({MONTHS})\s+)?(\d{{4}})\s*[-\u2013to]+\s*"
        rf"(?:({MONTHS})\s+)?(\d{{4}}|present|current)"
    )
    match = re.search(pattern, text.lower())
    if not match:
        return None, None

    start_month, start_year, end_month, end_year = match.groups()

    def build_date(month_str, year_str):
        if year_str in ("present", "current"):
            return datetime.now()
        month_num = 1
        if month_str:
            month_map = {
                "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
            }
            month_num = month_map.get(month_str[:3], 1)
        return datetime(int(year_str), month_num, 1)

    start_date = build_date(start_month, start_year)
    end_date = build_date(end_month, end_year)
    return start_date, end_date


def extract_experience_entries(experience_section_text: str) -> list[dict]:
    lines = [l for l in experience_section_text.split("\n") if l.strip()]

    raw_entries = []
    for i, line in enumerate(lines):
        start_date, end_date = parse_date_range(line)
        if start_date and end_date and i > 0:
            title_line = lines[i - 1].strip()
            if not (title_line.startswith("-") or title_line.startswith("\u2022")):
                raw_entries.append({
                    "title_line": title_line,
                    "start_date": start_date,
                    "end_date": end_date,
                    "date_line_index": i,
                })

    entries = []
    for idx, entry in enumerate(raw_entries):
        bullets_start = entry["date_line_index"] + 1
        bullets_end = (
            len(lines) if idx == len(raw_entries) - 1
            else lines.index(raw_entries[idx + 1]["title_line"], bullets_start)
        )
        bullets = [
            l.strip().lstrip("-\u2022 ")
            for l in lines[bullets_start:bullets_end]
            if l.strip().startswith("-") or l.strip().startswith("\u2022")
        ]

        duration_months = max(
            1, round((entry["end_date"] - entry["start_date"]).days / 30)
        )
        entries.append({
            "title_line": entry["title_line"],
            "start_date": entry["start_date"].isoformat(),
            "end_date": entry["end_date"].isoformat(),
            "duration_months": duration_months,
            "bullets": bullets,
        })

    return entries


def extract_education_entries(education_section_text: str) -> list[dict]:
    lines = [l.strip() for l in education_section_text.split("\n") if l.strip()]
    entries = []
    cgpa_pattern = re.compile(r"(cgpa|gpa)\s*[:\-]?\s*([\d.]+)(?:\s*/\s*[\d.]+)?", re.IGNORECASE)

    for line in lines:
        cgpa_match = cgpa_pattern.search(line)
        has_year = re.search(r"\d{4}", line)

        if has_year:
            entries.append({
                "raw_text": line,
                "gpa": cgpa_match.group(2) if cgpa_match else None,
            })
        elif cgpa_match and entries:
            entries[-1]["gpa"] = cgpa_match.group(2)

    return entries


def parse_resume(resume_text: str) -> dict:
    sections = split_into_sections(resume_text)
    skills = extract_skills(resume_text)
    experience_entries = extract_experience_entries(sections.get("experience", ""))
    education_entries = extract_education_entries(sections.get("education", ""))
    total_experience_months = sum(e["duration_months"] for e in experience_entries)

    return {
        "skills": skills,
        "experience": experience_entries,
        "education": education_entries,
        "total_experience_months": total_experience_months,
        "used_spacy": _NLP is not None,
    }


if __name__ == "__main__":
    import json
    sys.path.insert(0, str(Path(__file__).parent))
    from extract_pdf import extract_resume_text

    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "sample_data/sample_resume.pdf"
    raw_text = extract_resume_text(pdf_path)
    structured = parse_resume(raw_text)

    print("=" * 60)
    print(f"Structured extraction (spaCy available: {structured['used_spacy']})")
    print("=" * 60)
    print(json.dumps(structured, indent=2))