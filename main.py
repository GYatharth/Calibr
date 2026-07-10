"""
Calibr — main FastAPI application entry point.

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import engine, Base, SessionLocal
from app.db import models
from app.api.scoring_router import router as scoring_router
from app.api.auth_router import router as auth_router
from app.api.jd_router import router as jd_router
from app.api.batch_router import router as batch_router
from app.api.rankings_router import router as rankings_router
from app.api.candidate_router import router as candidate_router
from app.api.rate_limiter import limiter
from app.api.upload_router import router as upload_router
from app.api.interview_router import router as interview_router
from app.api.notes_router import router as notes_router
from app.api.skill_gap_router import router as skill_gap_router
from app.api.analytics_router import router as analytics_router
from app.api.resume_improve_router import router as resume_improve_router
from app.api.history_router import router as history_router

Base.metadata.create_all(bind=engine)


def run_migrations():
    """
    create_all() only creates missing tables — it never alters existing
    ones. Columns added to models after the table already exists in the
    Neon DB need an explicit ALTER TABLE here.
    """
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE candidates ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)"
        ))


def create_default_jd():
    db: Session = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == 1).first()
        if not user:
            user = models.User(
                id=1,
                email="default@calibr.dev",
                hashed_password="placeholder",
            )
            db.add(user)
            db.flush()

        existing = db.query(models.JobDescription).filter(
            models.JobDescription.id == 1
        ).first()
        if not existing:
            jd = models.JobDescription(
                id=1,
                owner_id=1,
                raw_text="Default placeholder JD",
                required_skills=[],
                required_experience_years=None,
            )
            db.add(jd)
            db.commit()
    finally:
        db.close()


app = FastAPI(
    title="Calibr",
    description="Hybrid resume screening with multi-signal scoring",
    version="0.1.0",
)

# CORS — allow React frontend to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://calibr-two.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
def startup_event():
    run_migrations()
    create_default_jd()


# Register routers
app.include_router(auth_router)
app.include_router(jd_router)
app.include_router(scoring_router)
app.include_router(batch_router)
app.include_router(rankings_router)
app.include_router(candidate_router)
app.include_router(upload_router)
app.include_router(interview_router)
app.include_router(notes_router)
app.include_router(skill_gap_router)
app.include_router(analytics_router)
app.include_router(resume_improve_router)
app.include_router(history_router)

@app.get("/")
def root():
    return {"status": "ok", "message": "Calibr API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}