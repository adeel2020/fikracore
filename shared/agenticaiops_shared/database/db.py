"""Database configuration and session management with intelligent host fallback."""

import os
import socket
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from agenticaiops_shared.config import settings

logger = logging.getLogger(__name__)

def _resolve_database_url() -> str:
    url = settings.database_url
    if not url:
        db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(db_dir, exist_ok=True)
        return f"sqlite:///{os.path.join(db_dir, 'app.db')}"

    # Handle host.docker.internal when running outside Docker container
    if "host.docker.internal" in url:
        try:
            socket.gethostbyname("host.docker.internal")
        except socket.gaierror:
            # Cannot resolve host.docker.internal, switch to localhost
            url = url.replace("host.docker.internal", "127.0.0.1")

    # Verify if Postgres is reachable, otherwise fallback to SQLite
    if url.startswith("postgresql"):
        try:
            test_engine = create_engine(url, connect_args={"connect_timeout": 2})
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            test_engine.dispose()
            return url
        except Exception as e:
            logger.info("PostgreSQL database unreachable (%s), falling back to local SQLite.", e)
            db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            os.makedirs(db_dir, exist_ok=True)
            return f"sqlite:///{os.path.join(db_dir, 'app.db')}"

    return url

DATABASE_URL = _resolve_database_url()

# Create engine
engine_args = {"echo": False}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    engine_args["pool_size"] = 10
    engine_args["max_overflow"] = 20

engine = create_engine(DATABASE_URL, **engine_args)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database - create all tables."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning("Database table creation skipped: %s", e)
