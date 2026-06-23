"""
Day 1: PDF text extraction.

Extracts raw text from resume PDFs. Uses pdfplumber as the primary
extractor since it handles layout (columns, tables) better than
PyPDF2, which is kept as a fallback for PDFs that pdfplumber chokes on
(e.g. some scanned-then-OCR'd or unusually encoded files).

This module deliberately does NOT try to understand the text yet —
that's Day 3 (structured extraction). Today's only job is: PDF in,
clean raw text out.
"""

import pdfplumber
from PyPDF2 import PdfReader
from pathlib import Path


class PDFExtractionError(Exception):
    """Raised when both extraction methods fail on a given file."""
    pass


def extract_text_pdfplumber(pdf_path: str) -> str:
    """Primary extraction path. Better at preserving reading order
    across columns and tables than PyPDF2."""
    text_chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
    return "\n".join(text_chunks)


def extract_text_pypdf2(pdf_path: str) -> str:
    """Fallback extraction path. Simpler, sometimes succeeds where
    pdfplumber returns empty text (e.g. certain font-embedding quirks)."""
    reader = PdfReader(pdf_path)
    text_chunks = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_chunks.append(page_text)
    return "\n".join(text_chunks)


def extract_resume_text(pdf_path: str) -> str:
    """
    Extract raw text from a resume PDF.

    Tries pdfplumber first. Falls back to PyPDF2 if pdfplumber
    returns empty/near-empty text. Raises PDFExtractionError if
    both fail — this is a real, documented limitation, not silently
    swallowed.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"No file at {pdf_path}")

    text = ""
    try:
        text = extract_text_pdfplumber(pdf_path)
    except Exception as e:
        print(f"[warn] pdfplumber failed on {path.name}: {e}")

    # If pdfplumber got nothing useful, try the fallback.
    if len(text.strip()) < 20:
        try:
            text = extract_text_pypdf2(pdf_path)
        except Exception as e:
            print(f"[warn] PyPDF2 also failed on {path.name}: {e}")

    if len(text.strip()) < 20:
        raise PDFExtractionError(
            f"Could not extract usable text from {path.name}. "
            f"This may be a scanned/image-only PDF — out of scope for v1."
        )

    return text.strip()


if __name__ == "__main__":
    # Day 1 task: feed in ONE resume, print the raw extracted text.
    # Usage: python extract_pdf.py path/to/resume.pdf
    import sys

    if len(sys.argv) != 2:
        print("Usage: python extract_pdf.py <path_to_resume.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    try:
        raw_text = extract_resume_text(pdf_path)
        print("=" * 60)
        print(f"Extracted {len(raw_text)} characters from {pdf_path}")
        print("=" * 60)
        print(raw_text)
    except (FileNotFoundError, PDFExtractionError) as e:
        print(f"[error] {e}")
        sys.exit(1)