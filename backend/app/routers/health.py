"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="",
    tags=["System"],
)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the API service is healthy",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "healthy"}
                }
            }
        }
    }
)
async def health_check() -> HealthResponse:
    """Health check endpoint.
    
    Returns:
        HealthResponse: Health status
    """
    return HealthResponse(status="healthy")