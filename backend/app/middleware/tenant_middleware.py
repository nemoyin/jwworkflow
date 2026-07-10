"""ContextVar-based tenant context and FastAPI tenant dependency.

Provides ``get_tenant_id()`` (reads the current tenant ID from a ``ContextVar``)
and a ``get_current_tenant`` FastAPI dependency that returns the ``Tenant``
ORM instance for the authenticated user.

Works together with ``auth_middleware.get_current_user`` — that function
sets ``tenant_ctx_var`` after it successfully resolves a user from the JWT.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.context import tenant_ctx_var
from app.models.tenant import Tenant

security = HTTPBearer()


def get_tenant_id() -> str | None:
    """Return the tenant ID stored in the current context, or ``None``."""
    return tenant_ctx_var.get()


async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """FastAPI dependency: authenticate and return the current user's Tenant.

    Uses a lazy import of ``get_current_user`` (called as a regular function)
    to avoid a circular dependency between this module and ``auth_middleware``.
    """
    # Lazy import to break circular dependency
    from app.middleware.auth_middleware import get_current_user  # noqa: E402

    # Authenticate and retrieve user (this also sets tenant_ctx_var)
    current_user = await get_current_user(credentials=credentials, db=db)

    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="租户不存在"
        )
    return tenant
