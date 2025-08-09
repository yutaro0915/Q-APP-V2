"""Database connection pool management."""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from asyncpg import Pool

logger = logging.getLogger(__name__)

_pool: Optional[Pool] = None


async def get_db_pool() -> Pool:
    """Get or create the database connection pool.
    
    Returns:
        Pool: The database connection pool
        
    Raises:
        ValueError: If DATABASE_URL is not set
        asyncpg.PostgresConnectionError: If connection fails after retries
    """
    global _pool
    
    if _pool is not None:
        return _pool
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Creating database connection pool (attempt {attempt + 1}/{max_retries})")
            _pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                max_queries=50000,
            )
            logger.info("Database connection pool created successfully")
            return _pool
        except asyncpg.PostgresConnectionError as e:
            logger.error(f"Failed to create connection pool: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Max retries exceeded, giving up")
                raise


async def close_db_pool() -> None:
    """Close the database connection pool."""
    global _pool
    
    if _pool is not None:
        logger.info("Closing database connection pool")
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")


async def check_db_connection() -> bool:
    """Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        global _pool
        if _pool is None:
            return False  # No pool exists, return False
        
        async with _pool.acquire() as connection:
            result = await connection.fetchval("SELECT 1")
            return result == 1
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


@asynccontextmanager
async def get_db_connection():
    """Get a database connection from the pool.
    
    Usage:
        async with get_db_connection() as conn:
            result = await conn.fetch("SELECT * FROM users")
    
    Yields:
        Connection: A database connection
    """
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        yield connection