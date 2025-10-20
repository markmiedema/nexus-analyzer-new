"""
Tenant context manager for automatic query filtering.
Ensures all database queries are scoped to the current tenant.
"""

from contextvars import ContextVar
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import event
from sqlalchemy.orm.query import Query

# Context variable to store current tenant_id
_tenant_id_ctx: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)


class TenantContext:
    """
    Context manager for tenant-scoped database operations.

    Usage:
        with TenantContext(tenant_id):
            # All queries here are automatically filtered by tenant_id
            users = db.query(User).all()  # Only returns users for this tenant
    """

    def __init__(self, tenant_id: Optional[str]):
        self.tenant_id = tenant_id
        self.token = None

    def __enter__(self):
        """Set tenant context on enter."""
        self.token = _tenant_id_ctx.set(self.tenant_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Reset tenant context on exit."""
        _tenant_id_ctx.reset(self.token)


def get_current_tenant_id() -> Optional[str]:
    """
    Get the current tenant ID from context.

    Returns:
        str: Current tenant ID or None
    """
    return _tenant_id_ctx.get()


def set_tenant_filter(query: Query, entity) -> Query:
    """
    Automatically add tenant_id filter to queries for models that have tenant_id.

    Args:
        query: SQLAlchemy query object
        entity: Model entity being queried

    Returns:
        Query: Modified query with tenant filter applied
    """
    tenant_id = get_current_tenant_id()

    # If no tenant context, return query unchanged
    if not tenant_id:
        return query

    # If entity has tenant_id column, add filter
    if hasattr(entity, "tenant_id"):
        return query.filter(entity.tenant_id == tenant_id)

    return query


def setup_tenant_filter(session_class):
    """
    Set up automatic tenant filtering for a SQLAlchemy session class.

    This is an advanced feature that can automatically filter all queries.
    Use with caution - explicit is better than implicit for most cases.

    Args:
        session_class: SQLAlchemy session class to enhance
    """

    @event.listens_for(session_class, "after_attach")
    def receive_after_attach(session, instance):
        """Automatically set tenant_id when attaching instances."""
        tenant_id = get_current_tenant_id()
        if tenant_id and hasattr(instance, "tenant_id") and not instance.tenant_id:
            instance.tenant_id = tenant_id


def tenant_filter(model_class):
    """
    Helper function to apply tenant filter to a query.

    Usage:
        users = tenant_filter(db.query(User)).all()

    Args:
        query: SQLAlchemy query

    Returns:
        Query: Filtered query
    """
    tenant_id = get_current_tenant_id()
    if tenant_id and hasattr(model_class, "tenant_id"):
        return model_class.tenant_id == tenant_id
    return None
