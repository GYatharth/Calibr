"""
Calibr — main FastAPI application entry point.

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from app.db.database import engine, Base

# Create all tables on startup if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Calibr",
    description="Hybrid resume screening with multi-signal scoring",
    version="0.1.0",
)
@app.get("/")
def root():
    return {"status": "ok", "message": "Calibr API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}