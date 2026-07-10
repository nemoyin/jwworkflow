"""ContextVar-based tenant context holder.

This module exists as a standalone hub to avoid circular imports between
``auth_middleware`` and ``tenant_middleware``.  Both modules import the
single ``tenant_ctx_var`` from here.

Usage::

    from app.middleware.context import tenant_ctx_var

    # Inside a request handler / dependency:
    tenant_ctx_var.set(str(some_tenant_id))
    ...
    current_id: str | None = tenant_ctx_var.get()
"""

from contextvars import ContextVar

tenant_ctx_var: ContextVar[str | None] = ContextVar("tenant_id", default=None)
