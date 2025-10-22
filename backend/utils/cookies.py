"""
Cookie utilities for secure token management.
"""

from fastapi import Response
from config import settings


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """
    Set httpOnly cookies for access and refresh tokens.

    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token
    """
    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Prevents JavaScript access (XSS protection)
        secure=settings.COOKIE_SECURE,  # Only send over HTTPS in production
        samesite=settings.COOKIE_SAMESITE,  # CSRF protection
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )

    # Set refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # seconds
        domain=settings.COOKIE_DOMAIN,
        path="/api/v1/auth/refresh",  # Only sent to refresh endpoint
    )


def clear_auth_cookies(response: Response) -> None:
    """
    Clear authentication cookies on logout.

    Args:
        response: FastAPI Response object
    """
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth/refresh",
        domain=settings.COOKIE_DOMAIN,
    )


def get_token_from_cookie_or_header(request, cookie_name: str = "access_token") -> str | None:
    """
    Get token from cookie or Authorization header (fallback for backwards compatibility).

    Args:
        request: FastAPI Request object
        cookie_name: Name of the cookie containing the token

    Returns:
        str | None: Token if found, None otherwise
    """
    # Try cookie first (preferred method)
    token = request.cookies.get(cookie_name)
    if token:
        return token

    # Fallback to Authorization header for backwards compatibility
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    return None
