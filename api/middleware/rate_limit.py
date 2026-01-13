"""
Rate limiting middleware for API endpoints.
"""

from fastapi import HTTPException, Request, status
from typing import Dict
import time
from collections import defaultdict
from asyncio import Lock

# Rate limits
MAX_REQUESTS_PER_MINUTE = 100
MAX_REQUESTS_PER_SECOND = 10

# Store request counts by IP
request_counts: Dict[str, list] = defaultdict(list)
request_times: Dict[str, float] = {}
lock = Lock()

async def rate_limit_middleware(request: Request, call_next):
    """Middleware to enforce rate limiting."""
    # Get client IP
    client_ip = request.client.host
    if not client_ip:
        await call_next(request)
        return

    current_time = time.time()

    # Clean old requests (older than 1 minute)
    async with lock:
        # Remove requests older than 60 seconds
        cutoff_time = current_time - 60
        request_counts[client_ip] = [
            ts for ts in request_counts[client_ip]
            if ts > cutoff_time
        ]
        request_times[client_ip] = [
            ts for ts in request_times[client_ip]
            if ts > cutoff_time
        ]

    # Count requests in last second
    recent_count = len([
        ts for ts in request_counts[client_ip]
        if ts > current_time - 1
    ])

    # Count requests in last minute
    last_minute_count = len(request_counts[client_ip])

    # Check rate limits
    if recent_count >= MAX_REQUESTS_PER_SECOND:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {recent_count}/{MAX_REQUESTS_PER_SECOND} requests per second"
        )

    if last_minute_count >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {last_minute_count}/{MAX_REQUESTS_PER_MINUTE} requests per minute"
        )

    # Record this request
    request_counts[client_ip].append(current_time)
    request_times[client_ip].append(current_time)

    await call_next(request)
