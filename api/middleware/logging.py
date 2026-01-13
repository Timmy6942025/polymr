"""
Request and response logging middleware.
"""

from fastapi import Request
import time
import json
import logging

logger = logging.getLogger(__name__)

SENSITIVE_FIELDS = ["private_key", "password", "secret", "token"]

async def logging_middleware(request: Request, call_next):
    """Middleware to log all requests and responses."""
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    await call_next(request)

    # Log response time
    duration = time.time() - start_time
    logger.info(f"Request completed in {duration:.3f}s")
