from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/api/v1", tags=["System"])


@router.get("/health", summary="Health Check", response_model=dict)
def health() -> dict:
    return {"status": "healthy"}

