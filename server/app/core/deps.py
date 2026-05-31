from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine


def get_engine(request: Request) -> AsyncEngine:
    return request.app.state.engine


EngineDep = Annotated[AsyncEngine, Depends(get_engine)]


async def get_db_conn(engine: EngineDep) -> AsyncIterator[AsyncConnection]:
    """Request-scoped 도메인 DB connection + tx. CRUD 라우트용.

    tx는 여기서 시작. 라우트는 commit/rollback 신경 안 씀 — 정상 종료 시 자동
    commit, 예외 시 자동 rollback. LLM/장시간 작업 라우트는 사용 X — repository
    가 JIT으로 acquire.
    """
    async with engine.connect() as conn, conn.begin():
        yield conn


ConnDep = Annotated[AsyncConnection, Depends(get_db_conn)]
