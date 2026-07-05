"""
PDF upload endpoint.

POST /upload/resume
  - Accepts a PDF file
  - Extracts text using the existing extract_pdf.py pipeline
  - Returns the raw extracted text
  - Client then sends this text to POST /score as usual

This keeps the architecture clean: upload = extract text only,
scoring is still a separate step.
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

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    """
    Upload a resume PDF and extract its text.
    Returns the raw text for the client to use in POST /score.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    # Save to a temp file since extract_resume_text needs a file path
    try:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf"
        ) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        text = extract_resume_text(tmp_path)
        return {
            "filename": file.filename,
            "extracted_text": text,
            "char_count": len(text),
        }

    except PDFExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
    finally:
        # Always clean up the temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)