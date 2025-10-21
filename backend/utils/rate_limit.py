"""
Rate limiting utilities for the application.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from config import settings

# Initialize rate limiter
# This can be imported by both main.py and route files
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.RATE_LIMIT_ENABLED else [],
    storage_uri=settings.RATE_LIMIT_STORAGE_URL or settings.REDIS_URL,
    enabled=settings.RATE_LIMIT_ENABLED,
)
