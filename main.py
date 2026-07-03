"""
Calibr — main FastAPI application entry point.

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from sqlalchemy.orm import Session
from app.db.database import engine, Base, SessionLocal
from app.db import models
from app.api.scoring_router import router as scoring_router

# Create all tables on startup if they don't exist
Base.metadata.create_all(bind=engine)


def create_default_jd():
    """
    Creates a placeholder JD with id=1 if it doesn't exist.
    This unblocks the /score endpoint until the proper JD upload
    endpoint is built on Day 12.
    """
    db: Session = SessionLocal()
    try:
        existing = db.query(models.JobDescription).filter(
            models.JobDescription.id == 1
        ).first()
        if not existing:
            # Need a dummy user first since JD has owner_id FK
            user = db.query(models.User).filter(models.User.id == 1).first()
            if not user:
                user = models.User(
                    id=1,
                    email="default@calibr.dev",
                    hashed_password="placeholder",
                )
                db.add(user)
                db.flush()

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


@app.on_event("startup")
def startup_event():
    create_default_jd()


# Register routers
app.include_router(scoring_router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Calibr API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}