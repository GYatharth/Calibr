"""
PDF upload endpoint — updated to return structured parsed data.

POST /upload/resume
  - Accepts a PDF file
  - Extracts raw text
  - Also runs structured parsing (skills, experience, education)
  - Returns text + parsed data for frontend display
"""

import sys
import tempfile
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.api.auth import get_current_user
from app.db import models

sys.path.insert(0, str(Path(__file__).parent.parent / "parsing"))
from extract_pdf import extract_resume_text, PDFExtractionError
from parse_resume import parse_resume

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    tmp_path = None
    try:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        # Extract raw text
        text = extract_resume_text(tmp_path)

        # Parse structured data
        parsed = parse_resume(text)

        return {
            "filename": file.filename,
            "extracted_text": text,
            "char_count": len(text),
            "parsed": {
                "contact": parsed.get("contact", {}),
                "skills": parsed.get("skills", []),
                "total_experience_months": parsed.get("total_experience_months", 0),
                "experience": [
                    {
                        "title_line": exp.get("title_line", ""),
                        "duration_months": exp.get("duration_months", 0),
                        "start_date": exp.get("start_date", ""),
                        "end_date": exp.get("end_date", ""),
                        "bullets": exp.get("bullets", []),
                    }
                    for exp in parsed.get("experience", [])
                ],
                "education": parsed.get("education", []),
                "certifications": parsed.get("certifications", []),
                "projects": [
                    {
                        "name": p.get("name", ""),
                        "bullets": p.get("bullets", []),
                    }
                    for p in parsed.get("projects", [])
                ],
            }
        }

    except PDFExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)