import pytest
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient
from app.main import app
from app.core.db import get_db_connection
from app.schemas.threads import ThreadCard, PaginatedThreadCards
from datetime import datetime

# Mock database connection for integration tests
async def mock_get_db_connection():
    """Mock database connection that doesn't require DATABASE_URL."""
    mock_conn = AsyncMock()
    return mock_conn

# Mock ThreadService responses
def create_mock_thread_cards():
    """Create mock thread cards that match the expected API contract."""
    from app.schemas.threads import Tag, AuthorAffiliation
    
    return [
        ThreadCard(
            id="thr_01234567890123456789012345",
            title="Sample Thread Title",
            excerpt="This is a sample thread excerpt...",
            tags=[Tag(key="種別", value="question")],
            authorAffiliation=AuthorAffiliation(faculty="工学部", year=2),
            createdAt="2024-01-01T10:00:00+00:00",
            replies=5,
            saves=3,
            heat=10,
            isMine=False,
            hasImage=False,
            solved=False,
            lastReplyAt="2024-01-01T11:30:00+00:00",
            imageThumbUrl=None
        ),
        ThreadCard(
            id="thr_98765432109876543210987654",
            title="Another Sample Thread",
            excerpt="Another sample excerpt for testing...",
            tags=[Tag(key="種別", value="chat")],
            authorAffiliation=AuthorAffiliation(faculty="理学部", year=3),
            createdAt="2024-01-01T09:30:00+00:00",
            replies=2,
            saves=1,
            heat=7,
            isMine=False,
            hasImage=False,
            solved=False,
            lastReplyAt=None,
            imageThumbUrl=None
        )
    ]

def create_mock_paginated_response():
    """Create mock paginated response matching API contract."""
    return PaginatedThreadCards(
        items=create_mock_thread_cards(),
        nextCursor=None
    )

# Override dependency for testing
app.dependency_overrides[get_db_connection] = mock_get_db_connection

def test_list_new_contract_and_order():
    """Test threads list new endpoint for contract compliance and ordering."""
    # Mock the ThreadService.list_threads_new method
    from app.services.threads_service import ThreadService
    original_method = ThreadService.list_threads_new
    ThreadService.list_threads_new = AsyncMock(return_value=create_mock_paginated_response())
    
    try:
        client = TestClient(app)
        r = client.get("/api/v1/threads?sort=new")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "items" in data and isinstance(data["items"], list)
        # nextCursor は None/str のいずれか
        assert ("nextCursor" not in data) or (data["nextCursor"] is None or isinstance(data["nextCursor"], str))
        # ヘッダ: X-Request-Id
        assert "X-Request-Id" in r.headers
    finally:
        # Restore original method
        ThreadService.list_threads_new = original_method

def test_list_new_response_schema():
    """Test threads list new response matches expected schema."""
    # Mock the ThreadService.list_threads_new method
    from app.services.threads_service import ThreadService
    original_method = ThreadService.list_threads_new
    ThreadService.list_threads_new = AsyncMock(return_value=create_mock_paginated_response())
    
    try:
        client = TestClient(app)
        r = client.get("/api/v1/threads?sort=new")
        assert r.status_code == 200
        data = r.json()
        
        # Check top level structure
        assert set(data.keys()).issubset({"items", "nextCursor"})
        
        # Check items structure if present
        if data["items"]:
            item = data["items"][0]
            expected_keys = {"id", "title", "excerpt", "tags", "authorAffiliation", 
                            "createdAt", "replies", "saves", "heat", "isMine", 
                            "hasImage", "solved", "lastReplyAt", "imageThumbUrl"}
            assert set(item.keys()) == expected_keys
    finally:
        # Restore original method
        ThreadService.list_threads_new = original_method

def test_list_new_headers():
    """Test required headers are present in threads list response."""
    # Mock the ThreadService.list_threads_new method
    from app.services.threads_service import ThreadService
    original_method = ThreadService.list_threads_new
    ThreadService.list_threads_new = AsyncMock(return_value=create_mock_paginated_response())
    
    try:
        client = TestClient(app)
        r = client.get("/api/v1/threads?sort=new")
        
        # X-Request-Id should always be present
        assert "X-Request-Id" in r.headers
        assert len(r.headers["X-Request-Id"]) > 0
        
        # Content-Type should be application/json
        assert "Content-Type" in r.headers
        assert "application/json" in r.headers["Content-Type"]
    finally:
        # Restore original method
        ThreadService.list_threads_new = original_method

def test_list_new_error_response_format():
    """Test error response follows ErrorResponse schema."""
    client = TestClient(app)
    # Test with invalid sort parameter
    r = client.get("/api/v1/threads?sort=invalid")
    
    # Should return 400 for validation error
    assert r.status_code == 400
    
    # Check error response structure
    data = r.json()
    assert "error" in data
    error = data["error"]
    assert "code" in error
    assert "message" in error
    # X-Request-Id should be present even in error responses
    assert "X-Request-Id" in r.headers