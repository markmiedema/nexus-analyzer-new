"""
Tenant identification middleware for multi-tenancy support.
Extracts tenant from subdomain and adds to request state.
"""

from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from models.tenant import Tenant
from database import SessionLocal


class TenantMiddleware:
    """
    Middleware to identify tenant from subdomain.

    Extracts tenant from request hostname (subdomain.domain.com)
    and adds tenant_id to request state.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        """Process request and add tenant context."""

        # Extract tenant from hostname
        tenant_subdomain = self._extract_subdomain(request)

        # Store subdomain in request state
        request.state.tenant_subdomain = tenant_subdomain
        request.state.tenant_id = None
        request.state.tenant = None

        # If subdomain provided, look up tenant
        if tenant_subdomain:
            db = SessionLocal()
            try:
                tenant = db.query(Tenant).filter(
                    Tenant.subdomain == tenant_subdomain
                ).first()

                if tenant:
                    request.state.tenant_id = str(tenant.tenant_id)
                    request.state.tenant = tenant
            finally:
                db.close()

        response = await call_next(request)
        return response

    def _extract_subdomain(self, request: Request) -> Optional[str]:
        """
        Extract subdomain from request hostname.

        Examples:
            - demo.nexus-analyzer.com -> "demo"
            - nexus-analyzer.com -> None
            - localhost:8000 -> None
            - demo.localhost:8000 -> "demo"

        Args:
            request: FastAPI request object

        Returns:
            str: Subdomain if present, None otherwise
        """
        host = request.headers.get("host", "")

        # Remove port if present
        if ":" in host:
            host = host.split(":")[0]

        # Split by dots
        parts = host.split(".")

        # If localhost or IP, check for subdomain
        if parts[0] in ["localhost", "127"] or parts[-1].isdigit():
            # localhost or IP without subdomain
            if len(parts) <= 1:
                return None
            # demo.localhost or demo.127.0.0.1
            return parts[0] if len(parts) > 1 else None

        # For regular domains (example.com)
        if len(parts) < 3:
            # No subdomain (just domain.com or domain.co.uk)
            return None

        # Extract subdomain (first part)
        # Skip common prefixes like www
        subdomain = parts[0]
        if subdomain == "www":
            return None

        return subdomain


def get_current_tenant(request: Request) -> Optional[Tenant]:
    """
    Dependency to get current tenant from request state.

    Usage:
        @app.get("/resource")
        def get_resource(tenant: Tenant = Depends(get_current_tenant)):
            if not tenant:
                raise HTTPException(status_code=400, detail="Tenant required")
            # ... use tenant

    Args:
        request: FastAPI request object

    Returns:
        Tenant: Current tenant if found, None otherwise
    """
    return getattr(request.state, "tenant", None)


def require_tenant(request: Request) -> Tenant:
    """
    Dependency to require a tenant (raises 400 if not found).

    Usage:
        @app.get("/resource")
        def get_resource(tenant: Tenant = Depends(require_tenant)):
            # tenant is guaranteed to exist here

    Args:
        request: FastAPI request object

    Returns:
        Tenant: Current tenant

    Raises:
        HTTPException: 400 if tenant not found
    """
    tenant = getattr(request.state, "tenant", None)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant identification required. Please access via subdomain."
        )

    return tenant
