from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Alembic Config object
config = context.config

# Set up loggers from the ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import app metadata for autogenerate support
from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402


def _get_sync_url() -> str:
    """Convert async-only database URLs to sync equivalents for Alembic.

    Alembic's online migration runner uses a sync SQLAlchemy engine, so
    async drivers (aiosqlite, asyncpg) must be replaced with their sync
    counterparts.
    """
    url = settings.DATABASE_URL
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://")
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    return url


config.set_main_option("sqlalchemy.url", _get_sync_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL, not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates a sync Engine from the config and associates a connection.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
