"""ContextVar-based tenant context and FastAPI tenant dependency.

Provides ``get_tenant_id()`` (reads the current tenant ID from a ``ContextVar``)
and re-exports ``get_current_tenant`` from ``auth_middleware`` (which uses
``Depends(get_current_user)`` — no duplicate JWT decode or DB query).

Works together with ``auth_middleware.get_current_user`` — that function
sets ``tenant_ctx_var`` after it successfully resolves a user from the JWT.
"""

from app.middleware.auth_middleware import get_current_tenant
from app.middleware.context import tenant_ctx_var


def get_tenant_id() -> str | None:
    """Return the tenant ID stored in the current context, or ``None``."""
    return tenant_ctx_var.get()
