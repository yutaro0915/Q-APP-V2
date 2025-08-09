"""Profile schemas."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class MyProfile(BaseModel):
    """My profile DTO with all fields visible to owner."""
    id: str = Field(serialization_alias="userId")
    faculty: Optional[str]
    year: Optional[int]
    faculty_public: bool
    year_public: bool
    created_at: Optional[str]


class PublicProfile(BaseModel):
    """Public profile DTO with privacy filtering applied."""
    id: str
    faculty: Optional[str]
    year: Optional[int]
    created_at: Optional[str]


class UpdateProfileRequest(BaseModel):
    """Request DTO for updating profile."""
    faculty: Optional[str] = Field(None, max_length=50)
    year: Optional[int] = Field(None, ge=1, le=10)
    faculty_public: Optional[bool] = None
    year_public: Optional[bool] = None

    @field_validator('faculty')
    @classmethod
    def validate_faculty(cls, v):
        if v is not None and len(v) > 50:
            raise ValueError('faculty must be 50 characters or less')
        return v

    @field_validator('year')
    @classmethod
    def validate_year(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('year must be between 1 and 10')
        return v