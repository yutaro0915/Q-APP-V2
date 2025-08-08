"""Test database connection pool functionality."""
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch, create_autospec

import asyncpg
import pytest


@pytest.mark.asyncio
async def test_get_db_pool_creates_pool():
    """Test that get_db_pool creates a connection pool."""
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
        # Mock at the module level where it's imported
        with patch("app.core.db.asyncpg") as mock_asyncpg:
            mock_pool = MagicMock()
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            
            import app.core.db
            app.core.db._pool = None  # Reset global pool
            
            pool = await app.core.db.get_db_pool()
            
            assert pool == mock_pool
            mock_asyncpg.create_pool.assert_called_once_with(
                "postgresql://test:test@localhost/test",
                min_size=5,
                max_size=20,
                command_timeout=60,
                max_queries=50000,
            )


@pytest.mark.asyncio
async def test_get_db_pool_returns_existing_pool():
    """Test that get_db_pool returns existing pool if already created."""
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
        with patch("app.core.db.asyncpg") as mock_asyncpg:
            mock_pool = MagicMock()
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            
            # Import after patching to reset module state
            import app.core.db
            app.core.db._pool = None  # Reset global pool
            
            pool1 = await app.core.db.get_db_pool()
            pool2 = await app.core.db.get_db_pool()
            
            assert pool1 == pool2
            mock_asyncpg.create_pool.assert_called_once()  # Should only create once


@pytest.mark.asyncio
async def test_get_db_pool_missing_database_url():
    """Test that get_db_pool raises error when DATABASE_URL is missing."""
    with patch.dict(os.environ, {}, clear=True):
        # Import after clearing env to test missing DATABASE_URL
        import app.core.db
        app.core.db._pool = None  # Reset global pool
        
        with pytest.raises(ValueError, match="DATABASE_URL environment variable is not set"):
            await app.core.db.get_db_pool()


@pytest.mark.asyncio
async def test_get_db_pool_with_retry():
    """Test that get_db_pool retries on connection failure."""
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
        with patch("app.core.db.asyncpg") as mock_asyncpg:
            # Fail twice, then succeed
            mock_pool = MagicMock()
            mock_asyncpg.create_pool = AsyncMock(side_effect=[
                asyncpg.PostgresConnectionError("Connection failed"),
                asyncpg.PostgresConnectionError("Connection failed"),
                mock_pool
            ])
            mock_asyncpg.PostgresConnectionError = asyncpg.PostgresConnectionError
            
            with patch("asyncio.sleep", new_callable=AsyncMock):  # Mock sleep to speed up test
                import app.core.db
                app.core.db._pool = None  # Reset global pool
                
                pool = await app.core.db.get_db_pool()
                
                assert pool == mock_pool
                assert mock_asyncpg.create_pool.call_count == 3


@pytest.mark.asyncio
async def test_get_db_pool_max_retries_exceeded():
    """Test that get_db_pool raises after max retries."""
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
        with patch("app.core.db.asyncpg") as mock_asyncpg:
            mock_asyncpg.create_pool = AsyncMock(side_effect=asyncpg.PostgresConnectionError("Connection failed"))
            mock_asyncpg.PostgresConnectionError = asyncpg.PostgresConnectionError
            
            with patch("asyncio.sleep", new_callable=AsyncMock):  # Mock sleep to speed up test
                import app.core.db
                app.core.db._pool = None  # Reset global pool
                
                with pytest.raises(asyncpg.PostgresConnectionError):
                    await app.core.db.get_db_pool()
                
                assert mock_asyncpg.create_pool.call_count == 3  # Should try 3 times


@pytest.mark.asyncio
async def test_close_db_pool():
    """Test that close_db_pool closes the connection pool."""
    mock_pool = AsyncMock()
    
    import app.core.db
    app.core.db._pool = mock_pool
    
    await app.core.db.close_db_pool()
    
    mock_pool.close.assert_called_once()
    assert app.core.db._pool is None


@pytest.mark.asyncio
async def test_close_db_pool_when_no_pool():
    """Test that close_db_pool handles case when no pool exists."""
    import app.core.db
    app.core.db._pool = None
    
    # Should not raise any error
    await app.core.db.close_db_pool()
    
    assert app.core.db._pool is None


@pytest.mark.asyncio
async def test_check_db_connection_success():
    """Test that check_db_connection returns True when connection is successful."""
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
        mock_pool = MagicMock()
        mock_connection = AsyncMock()
        mock_connection.fetchval = AsyncMock(return_value=1)
        
        # Create a proper async context manager
        class MockAcquire:
            async def __aenter__(self):
                return mock_connection
            async def __aexit__(self, *args):
                pass
        
        mock_pool.acquire.return_value = MockAcquire()
        
        import app.core.db
        app.core.db._pool = mock_pool
        
        result = await app.core.db.check_db_connection()
        
        assert result is True
        mock_connection.fetchval.assert_called_once_with("SELECT 1")


@pytest.mark.asyncio
async def test_check_db_connection_failure():
    """Test that check_db_connection returns False when connection fails."""
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
        import app.core.db
        app.core.db._pool = None  # No pool
        
        result = await app.core.db.check_db_connection()
        
        assert result is False


@pytest.mark.asyncio
async def test_get_db_connection_context_manager():
    """Test get_db_connection as async context manager."""
    mock_pool = MagicMock()
    mock_connection = AsyncMock()
    
    # Create a proper async context manager
    class MockAcquire:
        async def __aenter__(self):
            return mock_connection
        async def __aexit__(self, *args):
            pass
    
    mock_pool.acquire.return_value = MockAcquire()
    
    from app.core.db import get_db_connection
    
    with patch("app.core.db._pool", mock_pool):
        async with get_db_connection() as conn:
            assert conn == mock_connection
        
        mock_pool.acquire.assert_called_once()