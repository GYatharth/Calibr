"""
Database models (SQLAlchemy ORM).

Tables:
  - users           : recruiter accounts (added for Phase 4 auth)
  - job_descriptions: JDs uploaded by recruiters
  - candidates      : resumes uploaded against a JD
  - scores          : scoring results per candidate
  - explanations    : LLM explanation per score
  - scoring_jobs    : batch processing job tracking
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text,
    DateTime, ForeignKey, JSON, Boolean
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active     = Column(Boolean, default=True)
    role          = Column(String, default="recruiter")
    created_at    = Column(DateTime, default=datetime.utcnow)

    job_descriptions = relationship("JobDescription", back_populates="owner")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id                      = Column(Integer, primary_key=True, index=True)
    owner_id                = Column(Integer, ForeignKey("users.id"), nullable=False)
    raw_text                = Column(Text, nullable=False)
    required_skills         = Column(JSON)
    required_experience_years = Column(Integer, nullable=True)
    created_at              = Column(DateTime, default=datetime.utcnow)

    owner      = relationship("User", back_populates="job_descriptions")
    candidates = relationship("Candidate", back_populates="job_description")
    jobs       = relationship("ScoringJob", back_populates="job_description")


class Candidate(Base):
    __tablename__ = "candidates"

    id                     = Column(Integer, primary_key=True, index=True)
    jd_id                  = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    raw_resume_text        = Column(Text)
    extracted_skills       = Column(JSON)
    extracted_experience   = Column(JSON)
    total_experience_months = Column(Integer)
    status                  = Column(String, default="pending")  # pending/shortlisted/rejected
    recruiter_notes         = Column(Text, nullable=True)
    parsed_at              = Column(DateTime, default=datetime.utcnow)

    job_description = relationship("JobDescription", back_populates="candidates")
    score           = relationship("Score", back_populates="candidate", uselist=False)


class Score(Base):
    __tablename__ = "scores"

    id                = Column(Integer, primary_key=True, index=True)
    candidate_id      = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    skill_match_score = Column(Float)
    semantic_score    = Column(Float)
    experience_score  = Column(Float)
    composite_score   = Column(Float)
    matched_skills    = Column(JSON)
    missing_skills    = Column(JSON)
    weights_used      = Column(JSON)
    computed_at       = Column(DateTime, default=datetime.utcnow)

    candidate   = relationship("Candidate", back_populates="score")
    explanation = relationship("Explanation", back_populates="score", uselist=False)


class Explanation(Base):
    __tablename__ = "explanations"

    id                = Column(Integer, primary_key=True, index=True)
    score_id          = Column(Integer, ForeignKey("scores.id"), nullable=False)
    explanation_text  = Column(Text)
    candidate_summary = Column(Text, nullable=True)
    missing_skills    = Column(JSON)
    generated_at      = Column(DateTime, default=datetime.utcnow)

    score = relationship("Score", back_populates="explanation")


class ScoringJob(Base):
    __tablename__ = "scoring_jobs"

    id               = Column(Integer, primary_key=True, index=True)
    jd_id            = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    status           = Column(String, default="pending")  # pending/processing/done/failed
    total_resumes    = Column(Integer, default=0)
    processed_resumes = Column(Integer, default=0)
    created_at       = Column(DateTime, default=datetime.utcnow)
    completed_at     = Column(DateTime, nullable=True)

    job_description = relationship("JobDescription", back_populates="jobs")