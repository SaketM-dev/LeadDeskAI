"""Database configuration.

When DATABASE_URL is absent, use a local SQLite file so the API and hosted
chatbot can start for UI/demo development. Database-backed product endpoints
still require the PostgreSQL schema and a real DATABASE_URL.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATABASE_CONFIGURED = bool(DATABASE_URL)

if DATABASE_CONFIGURED:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # Local-only fallback: enables health checks and the chatbot without
    # requiring database credentials. This is not a replacement for Supabase.
    engine = create_engine(
        f"sqlite:///{PROJECT_ROOT / '.local-demo.db'}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
