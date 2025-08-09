"""Reaction schemas for thread and comment reactions."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


# ID pattern as per spec
THREAD_ID_PATTERN = re.compile(r'^thr_[0-9A-HJKMNP-TV-Z]{26}$')
COMMENT_ID_PATTERN = re.compile(r'^cmt_[0-9A-HJKMNP-TV-Z]{26}$')
REACTION_ID_PATTERN = re.compile(r'^rcn_[0-9A-HJKMNP-TV-Z]{26}$')


class ReactionType(str, Enum):
    """Valid reaction types."""
    UP = "up"
    SAVE = "save"


class TargetType(str, Enum):
    """Valid target types for reactions."""
    THREAD = "thread"
    COMMENT = "comment"


class ReactionRequestThread(BaseModel):
    """Request body for thread reactions."""
    kind: ReactionType = Field(..., description="Type of reaction: 'up' or 'save'")
    
    @field_validator('kind')
    @classmethod
    def validate_kind(cls, v: ReactionType) -> ReactionType:
        """Validate that kind is either 'up' or 'save' for threads."""
        if v not in [ReactionType.UP, ReactionType.SAVE]:
            raise ValueError("Thread reactions must be 'up' or 'save'")
        return v


class ReactionRequestComment(BaseModel):
    """Request body for comment reactions."""
    kind: ReactionType = Field(..., description="Type of reaction: 'up' only")
    
    @field_validator('kind')
    @classmethod
    def validate_kind(cls, v: ReactionType) -> ReactionType:
        """Validate that kind is only 'up' for comments."""
        if v != ReactionType.UP:
            raise ValueError("Comment reactions must be 'up' only")
        return v


class ReactionInDB(BaseModel):
    """Internal DTO for reactions stored in database."""
    id: str = Field(..., description="Reaction ID in rcn_* format")
    target_id: str = Field(..., description="ID of target (thread or comment)")
    target_type: TargetType = Field(..., description="Type of target")
    user_id: str = Field(..., description="ID of user who reacted")
    reaction_type: ReactionType = Field(..., description="Type of reaction")
    
    @field_validator('id')
    @classmethod
    def validate_reaction_id(cls, v: str) -> str:
        """Validate reaction ID format."""
        if not REACTION_ID_PATTERN.match(v):
            raise ValueError(f"Invalid reaction ID format: {v}")
        return v
    
    @field_validator('target_id')
    @classmethod
    def validate_target_id(cls, v: str, info) -> str:
        """Validate target ID format based on target type."""
        # We need to check after target_type is set
        # This will be validated in model_validator instead
        return v
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate user ID format."""
        if not v.startswith('usr_'):
            raise ValueError(f"Invalid user ID format: {v}")
        return v
    
    def model_post_init(self, __context) -> None:
        """Validate target_id matches target_type after model initialization."""
        if self.target_type == TargetType.THREAD:
            if not THREAD_ID_PATTERN.match(self.target_id):
                raise ValueError(f"Invalid thread ID format: {self.target_id}")
        elif self.target_type == TargetType.COMMENT:
            if not COMMENT_ID_PATTERN.match(self.target_id):
                raise ValueError(f"Invalid comment ID format: {self.target_id}")