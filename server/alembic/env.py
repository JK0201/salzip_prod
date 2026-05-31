import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.core.config import settings
from app.db.tables import metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata


def _configure_context(connection=None, *, url: str | None = None) -> None:
    """compare_type/server_default 켜야 autogenerate가 컬럼 변경을 잡음."""
    context.configure(
        connection=connection,
        url=url,
        target_metadata=target_metadata,
        literal_binds=url is not None,
        dialect_opts={"paramstyle": "named"} if url is not None else {},
        compare_type=True,
        compare_server_default=True,
    )


def run_migrations_offline() -> None:
    _configure_context(url=settings.DATABASE_URL)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    _configure_context(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # 마이그레이션은 단발 작업 — NullPool로 connection 누적 방지
    engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
