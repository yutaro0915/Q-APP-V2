"""Thread and comment schemas."""
import re
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any


# ID pattern as per spec
ID_PATTERN = re.compile(r'^(usr|cre|ses|thr|cmt|att|rcn)_[0-9A-HJKMNP-TV-Z]{26}$')

# Image key pattern as per spec
IMAGE_KEY_PATTERN = re.compile(r'^uploads/\d{4}/(0[1-9]|1[0-2])/[A-Za-z0-9_.-]+\.(webp|jpg|jpeg|png)$')

# Valid tag keys
VALID_TAG_KEYS = {'種別', '場所', '締切', '授業コード'}

# Valid 種別 values (slugs)
VALID_KIND_VALUES = {'question', 'notice', 'recruit', 'chat'}


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


def create_excerpt(text: str, max_length: int = 120) -> str:
    """Create excerpt from text.
    
    - Replace newlines with spaces
    - Compress multiple spaces
    - Truncate to max_length and add ellipsis if needed
    """
    if not text:
        return ""
    
    # Replace newlines with spaces
    text = re.sub(r'[\r\n]+', ' ', text)
    
    # Compress multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Trim
    text = text.strip()
    
    # Truncate if needed
    if len(text) > max_length:
        return text[:max_length] + "…"
    
    return text


class Tag(BaseModel):
    """Tag model."""
    key: str
    value: str
    
    @field_validator('key')
    @classmethod
    def validate_key(cls, v: str) -> str:
        if v not in VALID_TAG_KEYS:
            raise ValueError(f"Invalid tag key: {v}")
        return v
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v: str, info) -> str:
        # Access the key from the values dict
        key = info.data.get('key')
        
        if key == '種別':
            if v not in VALID_KIND_VALUES:
                raise ValueError(f"Invalid 種別 value: {v}. Must be one of {VALID_KIND_VALUES}")
        elif key == '場所':
            if not v or len(v) > 50:
                raise ValueError(f"場所 must be 1..50 characters")
        elif key == '授業コード':
            if not v or len(v) > 32:
                raise ValueError(f"授業コード must be 1..32 characters")
        elif key == '締切':
            # Validate date format YYYY-MM-DD
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
                raise ValueError(f"締切 must be in YYYY-MM-DD format")
        
        return v


class CreateThreadRequest(BaseModel):
    """Create thread request model."""
    title: str = Field(..., min_length=1, max_length=60)
    body: Optional[str] = Field(default="", max_length=2000)
    tags: List[Tag] = Field(default_factory=list, max_length=4)
    imageKey: Optional[str] = None
    
    @field_validator('title')
    @classmethod
    def trim_title(cls, v: str) -> str:
        if not v:
            raise ValueError("title cannot be empty")
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty after trimming")
        if len(v) > 60:
            raise ValueError("title must be 1..60 characters")
        return v
    
    @field_validator('body')
    @classmethod
    def process_body(cls, v: Optional[str]) -> str:
        if v is None:
            return ""
        v = v.strip()
        if len(v) > 2000:
            raise ValueError("body must be 0..2000 characters")
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[Tag]) -> List[Tag]:
        if len(v) > 4:
            raise ValueError("Maximum 4 tags allowed")
        
        # Check for duplicate keys
        keys = [tag.key for tag in v]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate tag keys not allowed")
        
        return v
    
    @field_validator('imageKey')
    @classmethod
    def validate_image_key_field(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not validate_image_key(v):
            raise ValueError(f"Invalid imageKey format: {v}")
        return v


class CreateCommentRequest(BaseModel):
    """Create comment request model."""
    body: str = Field(..., min_length=1, max_length=1000)
    imageKey: Optional[str] = None
    
    @field_validator('body')
    @classmethod
    def trim_body(cls, v: str) -> str:
        if not v:
            raise ValueError("body cannot be empty")
        v = v.strip()
        if not v:
            raise ValueError("body cannot be empty after trimming")
        if len(v) > 1000:
            raise ValueError("body must be 1..1000 characters")
        return v
    
    @field_validator('imageKey')
    @classmethod
    def validate_image_key_field(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not validate_image_key(v):
            raise ValueError(f"Invalid imageKey format: {v}")
        return v


class AuthorAffiliation(BaseModel):
    """Author affiliation model."""
    faculty: Optional[str] = None
    year: Optional[int] = None


class ThreadCard(BaseModel):
    """Thread card model for list views."""
    id: str
    title: str
    excerpt: str
    tags: List[Tag]
    heat: int
    replies: int
    saves: int
    createdAt: str
    lastReplyAt: Optional[str] = None
    hasImage: bool
    imageThumbUrl: Optional[str] = None
    solved: bool
    authorAffiliation: Optional[AuthorAffiliation] = None
    isMine: Optional[bool] = None


class ThreadDetail(BaseModel):
    """Thread detail model."""
    id: str
    title: str
    body: str
    tags: List[Tag]
    upCount: int
    saveCount: int
    createdAt: str
    lastActivityAt: str
    solvedCommentId: Optional[str] = None
    hasImage: bool
    imageUrl: Optional[str] = None
    authorAffiliation: Optional[AuthorAffiliation] = None
    isMine: Optional[bool] = None


class Comment(BaseModel):
    """Comment model."""
    id: str
    body: str
    createdAt: str
    upCount: int
    hasImage: bool
    imageUrl: Optional[str] = None
    authorAffiliation: Optional[AuthorAffiliation] = None


class PaginatedThreadCards(BaseModel):
    """Paginated thread cards response."""
    items: List[ThreadCard]
    nextCursor: Optional[str] = None


class PaginatedComments(BaseModel):
    """Paginated comments response."""
    items: List[Comment]
    nextCursor: Optional[str] = None


class ThreadInDB(BaseModel):
    """Thread database model (internal)."""
    id: str
    author_id: str
    title: str
    body: str
    up_count: int
    save_count: int
    solved_comment_id: Optional[str] = None
    heat: float
    created_at: datetime
    last_activity_at: datetime
    deleted_at: Optional[datetime] = None