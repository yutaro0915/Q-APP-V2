"""Test thread schemas."""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas.threads import (
    Tag,
    CreateThreadRequest,
    CreateCommentRequest,
    AuthorAffiliation,
    ThreadCard,
    ThreadDetail,
    Comment,
    PaginatedThreadCards,
    PaginatedComments,
    ThreadInDB,
    validate_id_format,
    validate_image_key,
    create_excerpt
)


def test_tag_validation():
    """Test Tag validation."""
    # Valid tags
    tag1 = Tag(key="種別", value="question")
    assert tag1.key == "種別"
    assert tag1.value == "question"
    
    tag2 = Tag(key="場所", value="伊都キャンパス")
    assert tag2.key == "場所"
    
    tag3 = Tag(key="締切", value="2025-12-31")
    assert tag3.key == "締切"
    
    tag4 = Tag(key="授業コード", value="CS101")
    assert tag4.key == "授業コード"


def test_create_thread_request_validation():
    """Test CreateThreadRequest validation."""
    # Valid request with all fields
    request = CreateThreadRequest(
        title="Test Thread",
        body="This is a test body",
        tags=[Tag(key="種別", value="question")],
        imageKey="uploads/2025/08/test.webp"
    )
    assert request.title == "Test Thread"
    assert request.body == "This is a test body"
    assert len(request.tags) == 1
    
    # Valid request with minimal fields
    request2 = CreateThreadRequest(
        title="  Minimal Thread  "
    )
    assert request2.title == "Minimal Thread"  # Should be trimmed
    assert request2.body == ""  # Should default to empty string
    assert request2.tags == []
    
    # Invalid: empty title after trim
    with pytest.raises(ValidationError) as exc_info:
        CreateThreadRequest(title="   ")
    assert "title" in str(exc_info.value)
    
    # Invalid: title too long
    with pytest.raises(ValidationError) as exc_info:
        CreateThreadRequest(title="a" * 61)
    assert "title" in str(exc_info.value)
    
    # Invalid: body too long
    with pytest.raises(ValidationError) as exc_info:
        CreateThreadRequest(title="Valid", body="a" * 2001)
    assert "body" in str(exc_info.value)
    
    # Invalid: too many tags
    with pytest.raises(ValidationError) as exc_info:
        CreateThreadRequest(
            title="Valid",
            tags=[
                Tag(key="種別", value="question"),
                Tag(key="場所", value="location"),
                Tag(key="締切", value="2025-12-31"),
                Tag(key="授業コード", value="CS101"),
                Tag(key="授業コード", value="CS102")  # 5th tag, should fail
            ]
        )
    assert "tags" in str(exc_info.value) or "Maximum 4 tags" in str(exc_info.value)
    
    # Invalid: duplicate tag keys
    with pytest.raises(ValidationError) as exc_info:
        CreateThreadRequest(
            title="Valid",
            tags=[
                Tag(key="種別", value="question"),
                Tag(key="種別", value="notice")
            ]
        )
    assert "Duplicate tag key" in str(exc_info.value)
    
    # Invalid: invalid 種別 value
    with pytest.raises(ValidationError) as exc_info:
        CreateThreadRequest(
            title="Valid",
            tags=[Tag(key="種別", value="invalid")]
        )
    assert "種別" in str(exc_info.value)
    
    # Invalid: invalid image key format
    with pytest.raises(ValidationError) as exc_info:
        CreateThreadRequest(
            title="Valid",
            imageKey="invalid/path"
        )
    assert "imageKey" in str(exc_info.value)


def test_create_comment_request():
    """Test CreateCommentRequest validation."""
    # Valid request
    request = CreateCommentRequest(
        body="  This is a comment  ",
        imageKey="uploads/2025/08/image.png"
    )
    assert request.body == "This is a comment"  # Should be trimmed
    
    # Invalid: empty body
    with pytest.raises(ValidationError) as exc_info:
        CreateCommentRequest(body="   ")
    assert "body" in str(exc_info.value)
    
    # Invalid: body too long
    with pytest.raises(ValidationError) as exc_info:
        CreateCommentRequest(body="a" * 1001)
    assert "body" in str(exc_info.value)


def test_author_affiliation():
    """Test AuthorAffiliation model."""
    # With both fields
    affiliation = AuthorAffiliation(faculty="工学部", year=3)
    assert affiliation.faculty == "工学部"
    assert affiliation.year == 3
    
    # With only faculty
    affiliation2 = AuthorAffiliation(faculty="理学部")
    assert affiliation2.faculty == "理学部"
    assert affiliation2.year is None
    
    # With only year
    affiliation3 = AuthorAffiliation(year=1)
    assert affiliation3.faculty is None
    assert affiliation3.year == 1
    
    # Empty affiliation
    affiliation4 = AuthorAffiliation()
    assert affiliation4.faculty is None
    assert affiliation4.year is None


def test_thread_card():
    """Test ThreadCard model."""
    card = ThreadCard(
        id="thr_01HX123456789ABCDEFGHJKMNP",
        title="Test Thread",
        excerpt="This is an excerpt",
        tags=[Tag(key="種別", value="question")],
        heat=100,
        replies=5,
        saves=3,
        createdAt="2025-08-06T09:00:00Z",
        lastReplyAt="2025-08-06T10:00:00Z",
        hasImage=True,
        imageThumbUrl="https://example.com/image.webp",
        solved=True,
        authorAffiliation=AuthorAffiliation(faculty="工学部", year=3)
    )
    assert card.id == "thr_01HX123456789ABCDEFGHJKMNP"
    assert card.solved is True
    assert card.heat == 100


def test_thread_detail():
    """Test ThreadDetail model."""
    detail = ThreadDetail(
        id="thr_01HX123456789ABCDEFGHJKMNP",
        title="Test Thread",
        body="This is the full body",
        tags=[Tag(key="種別", value="question")],
        upCount=10,
        saveCount=5,
        createdAt="2025-08-06T09:00:00Z",
        lastActivityAt="2025-08-06T10:00:00Z",
        solvedCommentId="cmt_01HX123456789ABCDEFGHJKMNP",
        hasImage=False,
        imageUrl=None,
        authorAffiliation=None
    )
    assert detail.solvedCommentId == "cmt_01HX123456789ABCDEFGHJKMNP"
    assert detail.upCount == 10


def test_comment():
    """Test Comment model."""
    comment = Comment(
        id="cmt_01HX123456789ABCDEFGHJKMNP",
        body="This is a comment",
        createdAt="2025-08-06T09:00:00Z",
        upCount=5,
        hasImage=True,
        imageUrl="https://example.com/image.png",
        authorAffiliation=AuthorAffiliation(year=2)
    )
    assert comment.id == "cmt_01HX123456789ABCDEFGHJKMNP"
    assert comment.upCount == 5


def test_paginated_responses():
    """Test paginated response models."""
    # Thread cards pagination
    threads = PaginatedThreadCards(
        items=[
            ThreadCard(
                id="thr_01HX123456789ABCDEFGHJKMNP",
                title="Test",
                excerpt="Excerpt",
                tags=[],
                heat=0,
                replies=0,
                saves=0,
                createdAt="2025-08-06T09:00:00Z",
                hasImage=False,
                solved=False
            )
        ],
        nextCursor="eyJ2IjoxLCJhbmNob3IiOnsiaWQiOiJ0aHJfMDFIWDEyMzQ1Njc4OTBBQUNERFM="
    )
    assert len(threads.items) == 1
    assert threads.nextCursor is not None
    
    # Comments pagination
    comments = PaginatedComments(
        items=[
            Comment(
                id="cmt_01HX123456789ABCDEFGHJKMNP",
                body="Comment",
                createdAt="2025-08-06T09:00:00Z",
                upCount=0,
                hasImage=False
            )
        ],
        nextCursor=None
    )
    assert len(comments.items) == 1
    assert comments.nextCursor is None


def test_thread_in_db():
    """Test ThreadInDB internal model."""
    thread = ThreadInDB(
        id="thr_01HX123456789ABCDEFGHJKMNP",
        author_id="usr_01HX123456789ABCDEFGHJKMNP",
        title="Test Thread",
        body="Body text",
        up_count=10,
        save_count=5,
        solved_comment_id=None,
        heat=100.5,
        created_at=datetime.now(timezone.utc),
        last_activity_at=datetime.now(timezone.utc),
        deleted_at=None
    )
    assert thread.id.startswith("thr_")
    assert thread.author_id.startswith("usr_")
    assert thread.deleted_at is None


def test_validate_id_format():
    """Test ID format validation."""
    # Valid IDs (ULID charset: 0-9, A-H, J, K, M, N, P-T, V-Z)
    assert validate_id_format("usr_01HX123456789ABCDEFGHJKMNP") is True
    assert validate_id_format("thr_01HX123456789ABCDEFGHJKMNP") is True
    assert validate_id_format("cmt_01HX123456789ABCDEFGHJKMNP") is True
    assert validate_id_format("ses_01HX123456789ABCDEFGHJKMNP") is True
    assert validate_id_format("att_01HX123456789ABCDEFGHJKMNP") is True
    assert validate_id_format("rcn_01HX123456789ABCDEFGHJKMNP") is True
    
    # Invalid IDs
    assert validate_id_format("invalid_01HX123456789ABCDEFGHJKMNP") is False
    assert validate_id_format("usr_01HX123456789ABCDEFGHJKMN") is False  # Too short
    assert validate_id_format("usr_01HX123456789ABCDEFGHJKMNPQ") is False  # Too long
    assert validate_id_format("usr_01HX123456789ABCDEFGHIJKMN") is False  # Invalid char (I)
    assert validate_id_format("usr_01HX123456789ABCDEFGHJKMNO") is False  # Invalid char (O)
    assert validate_id_format("") is False
    assert validate_id_format("usr_") is False


def test_validate_image_key():
    """Test image key validation."""
    # Valid keys
    assert validate_image_key("uploads/2025/08/image.webp") is True
    assert validate_image_key("uploads/2025/12/test-file_123.png") is True
    assert validate_image_key("uploads/2025/01/IMG_001.jpeg") is True
    assert validate_image_key("uploads/2025/01/photo.jpg") is True
    
    # Invalid keys
    assert validate_image_key("uploads/25/08/image.webp") is False  # Wrong year format
    assert validate_image_key("uploads/2025/13/image.webp") is False  # Invalid month
    assert validate_image_key("uploads/2025/08/image.gif") is False  # Invalid extension
    assert validate_image_key("uploads/2025/08/") is False  # No filename
    assert validate_image_key("invalid/path/image.webp") is False
    assert validate_image_key("") is False


def test_create_excerpt():
    """Test excerpt creation."""
    # Normal text under 120 chars
    text = "This is a normal text that is under the limit."
    assert create_excerpt(text) == text
    
    # Text with newlines
    text_with_newlines = "This is line 1.\nThis is line 2.\r\nThis is line 3."
    assert create_excerpt(text_with_newlines) == "This is line 1. This is line 2. This is line 3."
    
    # Text with multiple spaces
    text_with_spaces = "This  has   multiple    spaces."
    assert create_excerpt(text_with_spaces) == "This has multiple spaces."
    
    # Text over 120 chars
    long_text = "a" * 121
    assert create_excerpt(long_text) == "a" * 120 + "…"
    
    # Text with exactly 120 chars
    exact_text = "a" * 120
    assert create_excerpt(exact_text) == exact_text
    
    # Empty text
    assert create_excerpt("") == ""
    
    # Text with only whitespace
    assert create_excerpt("   \n\r\n   ") == ""
    
    # Complex case: newlines, spaces, and over limit
    complex = "Line 1 with some text.\n\n  Line 2 with   spaces.\r\n" + "a" * 100
    excerpt = create_excerpt(complex)
    assert len(excerpt) <= 121  # 120 + ellipsis
    assert "…" in excerpt
    assert "\n" not in excerpt
    assert "  " not in excerpt  # No double spaces