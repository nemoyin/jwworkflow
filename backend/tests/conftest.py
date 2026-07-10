"""Pytest fixtures and test configuration.

Overrides DATABASE_URL to use SQLite for testing so tests can run
without an external PostgreSQL server. Registers a SQLAlchemy
@compiles handler for the PostgreSQL UUID type so it renders as
VARCHAR(36) when using SQLite.
"""

import os
import pathlib
import tempfile

# Override before any application imports to ensure
# app.config.settings picks up the test database URL.
# Use a temporary directory so concurrent/parallel runs don't conflict.
_test_db_dir = pathlib.Path(tempfile.mkdtemp())
_test_db_path = _test_db_dir / "test.db"

os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{_test_db_path.as_posix()}",
)
os.environ.setdefault("JWT_SECRET", "test-secret")

# ---------------------------------------------------------------------------
# Register a SQLAlchemy type-compiler so that the PostgreSQL UUID column
# type used by the ORM models works on SQLite (renders as VARCHAR(36)).
# This must be imported BEFORE any model imports happen.
# ---------------------------------------------------------------------------
from sqlalchemy.dialects.postgresql import UUID as PgUUID  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402


@compiles(PgUUID, "sqlite")
def _compile_pguuid_sqlite(element, compiler, **kw):
    """Render PostgreSQL UUID as VARCHAR(36) on SQLite."""
    return "VARCHAR(36)"


# ---------------------------------------------------------------------------
# Ensure tables are created before any test runs.  The app lifespan would
# normally do this, but TestClient(app) used without a context manager
# does NOT trigger the lifespan, so we do it at session scope here.
# ---------------------------------------------------------------------------
import asyncio  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    """Override the default event loop for session-scoped async fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def _setup_database(event_loop):
    """Create all ORM tables in the test database before any tests run.

    Imports the ORM models explicitly here so they are registered on
    ``Base.metadata`` before ``create_all`` is called.
    """
    from app.database import Base, engine
    from app.models import Tenant, User  # noqa: F401 — register on metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Dispose the engine so the file lock is released, then clean up.
    await engine.dispose()
    if _test_db_path.exists():
        _test_db_path.unlink()
    # Also remove the temp directory itself
    try:
        _test_db_dir.rmdir()
    except OSError:
        pass
