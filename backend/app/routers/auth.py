"""Authentication router."""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.db import get_db_pool
from app.util.errors import UnauthorizedException
from app.util.idgen import generate_id

router = APIRouter(prefix="/auth", tags=["auth"])


class BootstrapRequest(BaseModel):
    """Bootstrap request model."""
    device_secret: Optional[str] = None


class BootstrapResponse(BaseModel):
    """Bootstrap response model."""
    userId: str
    token: str
    expiresAt: str


def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token using SHA256."""
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/bootstrap", response_model=BootstrapResponse)
async def bootstrap(request: BootstrapRequest) -> BootstrapResponse:
    """Bootstrap authentication for a user.
    
    Creates a new user or retrieves existing user based on device_secret.
    Always creates a new session.
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Phase 1: Always create new user for simplicity
            # In Phase 2+, we'll implement proper device_secret handling
            user_id = generate_id("usr")
            query = """
                INSERT INTO users (id, role, created_at)
                VALUES ($1, 'student', $2)
            """
            await conn.execute(query, user_id, datetime.now(timezone.utc))
            
            # Create new session
            session_id = generate_id("ses")
            token = generate_token()
            token_hash = hash_token(token)
            
            # Get TTL from environment or default to 7 days
            ttl_hours = int(os.getenv("SESSION_TTL_HOURS", "168"))  # 7 days = 168 hours
            expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
            
            query = """
                INSERT INTO sessions (id, user_id, token_hash, expires_at, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """
            await conn.execute(
                query,
                session_id,
                user_id,
                token_hash,
                expires_at,
                datetime.now(timezone.utc)
            )
            
            return BootstrapResponse(
                userId=user_id,
                token=token,
                expiresAt=expires_at.isoformat().replace("+00:00", "Z")
            )