from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.engine import make_url

from app.core.config import settings


def _to_psycopg_url(sqlalchemy_url: str) -> str:
    """SQLAlchemy URL(+asyncpg) → psycopg URL. driver만 안전하게 떼어냄."""
    url = make_url(sqlalchemy_url)
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


@asynccontextmanager
async def lifespan_checkpointer() -> AsyncIterator[AsyncPostgresSaver]:
    """LangGraph checkpointer 전용 psycopg pool. 도메인 SQLAlchemy engine과 분리.

    psycopg-pool 기본값 사용 (min_size=4). `open=False` + 명시적 `await pool.open()`
    패턴으로 deprecation warning 회피.
    """
    conn_string = _to_psycopg_url(settings.DATABASE_URL)
    pool = AsyncConnectionPool(
        conninfo=conn_string,
        kwargs={"autocommit": True, "row_factory": dict_row},
        open=False,
    )
    await pool.open()
    try:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        yield checkpointer
    finally:
        await pool.close()
