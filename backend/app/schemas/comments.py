"""Comment schemas."""
import re
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, model_validator


# ID pattern as per spec
ID_PATTERN = re.compile(r'^(usr|cre|ses|thr|cmt|att|rcn)_[0-9A-HJKMNP-TV-Z]{26}$')

# Image key pattern as per spec  
IMAGE_KEY_PATTERN = re.compile(r'^uploads/\d{4}/(0[1-9]|1[0-2])/[A-Za-z0-9_.-]+\.(webp|jpg|jpeg|png)$')


def validate_id_format(id_str: str) -> bool:
    """Validate ID format."""
    if not id_str:
        return False
    return bool(ID_PATTERN.match(id_str))


def validate_image_key(key: str) -> bool:
    """Validate image key format."""
    if not key:
        return False
    return bool(IMAGE_KEY_PATTERN.match(key))


def clean_text(text: str) -> str:
    """Clean text by removing control characters but keeping newlines."""
    if not text:
        return ""
    # Remove null bytes and control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # Trim whitespace
    return text.strip()


class CreateCommentRequest(BaseModel):
    """Request to create a comment."""
    body: str = Field(..., min_length=1, max_length=1000)
    imageKey: Optional[str] = Field(None)
    
    @field_validator('body')
    def validate_body(cls, v: str) -> str:
        """Validate and clean body text."""
        cleaned = clean_text(v)
        if not cleaned or len(cleaned) < 1:
            raise ValueError("Body must contain at least 1 character")
        if len(cleaned) > 1000:
            raise ValueError("Body must not exceed 1000 characters")
        return cleaned
    
    @field_validator('imageKey')
    def validate_image_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate image key format."""
        if v is None:
            return None
        if not validate_image_key(v):
            raise ValueError(f"Invalid image key format: {v}")
        return v


class CommentInDB(BaseModel):
    """Internal comment representation from database."""
    id: str
    thread_id: str
    author_id: str
    body: str
    up_count: int = 0
    created_at: datetime
    deleted_at: Optional[datetime] = None
    
    @field_validator('id', 'thread_id', 'author_id')
    def validate_ids(cls, v: str) -> str:
        """Validate ID format."""
        if not validate_id_format(v):
            raise ValueError(f"Invalid ID format: {v}")
        return v


class AuthorAffiliation(BaseModel):
    """Author affiliation info."""
    faculty: Optional[str] = None
    year: Optional[int] = None


class Comment(BaseModel):
    """Public comment DTO."""
    id: str
    body: str
    createdAt: str  # ISO8601
    upCount: int
    hasImage: bool
    imageUrl: Optional[str] = None
    authorAffiliation: Optional[AuthorAffiliation] = None
    
    @field_validator('id')
    def validate_id(cls, v: str) -> str:
        """Validate comment ID format."""
        if not v.startswith('cmt_'):
            raise ValueError(f"Comment ID must start with 'cmt_': {v}")
        if not validate_id_format(v):
            raise ValueError(f"Invalid ID format: {v}")
        return v
    
    @field_validator('createdAt')
    def validate_created_at(cls, v: str) -> str:
        """Validate ISO8601 format."""
        try:
            # Parse to validate format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid ISO8601 format: {v}")
        return v


class CreatedResponse(BaseModel):
    """Response after creating a comment."""
    id: str
    createdAt: str  # ISO8601
    
    @field_validator('id')
    def validate_id(cls, v: str) -> str:
        """Validate comment ID format."""
        if not v.startswith('cmt_'):
            raise ValueError(f"Comment ID must start with 'cmt_': {v}")
        if not validate_id_format(v):
            raise ValueError(f"Invalid ID format: {v}")
        return v
    
    @field_validator('createdAt')
    def validate_created_at(cls, v: str) -> str:
        """Validate ISO8601 format."""
        try:
            # Parse to validate format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid ISO8601 format: {v}")
        return v


class PaginatedComments(BaseModel):
    """Paginated comments response."""
    items: List[Comment]
    nextCursor: Optional[str] = None