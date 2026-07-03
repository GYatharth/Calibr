"""
Database connection and session management.

Uses SQLAlchemy with Neon PostgreSQL. The DATABASE_URL is read
from the .env file — never hardcoded.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment. Check your .env file.")

# Neon requires SSL — psycopg2 handles this via the ?sslmode=require
# in the connection string automatically.
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a database session per request,
    and ensures it's closed when the request is done even if
    an exception is raised.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()