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
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./wealthlens.db")


async def init_db():
    """Initialize database engine and create tables."""
    global _engine, _session_factory

    if not HAS_ASYNC:
        print("Warning: asyncpg/aiosqlite not installed. DB features disabled.")
        return

    url = get_database_url()
    _engine = create_async_engine(url, echo=False)
    _session_factory = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


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
