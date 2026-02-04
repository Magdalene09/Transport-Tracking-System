"""
Database configuration and session management.

This module sets up the async SQLAlchemy engine and provides
session management utilities for database operations.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from typing import AsyncGenerator

from config import (
    DATABASE_URL, 
    DB_POOL_SIZE, 
    DB_MAX_OVERFLOW, 
    DB_POOL_TIMEOUT,
    SCHEMA_NAME
)
from models import Base

logger = logging.getLogger(__name__)

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=3600
)

# Session factory
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Yields:
        AsyncSession: Database session for the request
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """
    Check if the database connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def init_db() -> None:
    """
    Initialize the database schema and tables.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}"))
            logger.info(f"Schema \'{SCHEMA_NAME}\' ensured")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/verified")

        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")


async def dispose_db() -> None:
    """
    Dispose of the database connection pool.
    """
    await engine.dispose()
    logger.info("Database connection pool disposed")


async def get_db_stats() -> dict:
    """
    Get database connection pool statistics.
    """
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow()
    }
