"""
Async PostgreSQL connection management for WealthLens.
Uses SQLModel with asyncpg driver.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlmodel import SQLModel

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    HAS_ASYNC = True
except ImportError:
    HAS_ASYNC = False

_engine = None
_session_factory = None


def get_database_url() -> str:
    """Get database URL from environment (Supabase PostgreSQL connection string)."""
    return os.getenv("DATABASE_URL", "")


async def init_db():
    """Initialize database engine. Schema is managed by Supabase."""
    global _engine, _session_factory

    if not HAS_ASYNC:
        print("Warning: asyncpg not installed. DB features disabled.")
        return

    url = get_database_url()
    if not url:
        print("Warning: DATABASE_URL not set. DB features disabled.")
        return

    _engine = create_async_engine(url, echo=False)
    _session_factory = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator:
    """Get an async database session."""
    if not _session_factory:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
