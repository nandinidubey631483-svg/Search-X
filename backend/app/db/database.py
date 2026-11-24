"""
Database engine and transactional session management for SearchX.
Supports PostgreSQL in production and SQLite in testing.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from ..config import settings

Base = declarative_base()


class Database:
    """Manages database connection pool and transactional sessions."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        raw_url = database_url or settings.DATABASE_URL
        if raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql://", 1)
        self.url = raw_url
        connect_args = {}
        if self.url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        self.engine = create_engine(self.url, connect_args=connect_args)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self) -> None:
        """Create all tables registered with Base."""
        from . import models  # noqa: F401 - ensure models are registered
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all tables registered with Base."""
        from . import models  # noqa: F401 - ensure models are registered
        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Transactional session context manager.
        Automatically commits on successful block exit; rolls back on exception.
        """
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


# Default singleton database instance
_default_db = Database()


def get_database() -> Database:
    return _default_db


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database session."""
    with _default_db.session() as s:
        yield s
