"""
Authentication middleware for API key validation.
"""

from fastapi import HTTPException, Request, status
from typing import Optional

# Simple in-memory API key store (in production, use database)
VALID_API_KEYS: Set[str] = {"dev-api-key-12345"}

async def auth_middleware(request: Request, call_next):
    """Middleware to check for API key authentication."""
    # Read API key from headers
    api_key = request.headers.get("X-API-Key")

    # Skip auth for GET endpoints (read-only mode)
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        await call_next(request)
        return

    # Check API key for POST endpoints
    if not api_key or api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )

    await call_next(request)
