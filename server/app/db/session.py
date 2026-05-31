from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings


def create_db_engine() -> AsyncEngine:
    """도메인 DB engine 팩토리 (SQLAlchemy + asyncpg).

    sync `sqlalchemy.create_engine`과 이름 충돌 회피 위해 `create_db_engine`로 명명.
    """
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
    )
