"""Test fixtures.

이 fixture는 lifespan을 발동시키지 않으므로 `app.state.engine`/`checkpointer`가
초기화되지 않은 상태. DB가 필요한 통합 테스트는 별도 fixture로 lifespan 또는
의존성 override (FastAPI `dependency_overrides`)를 직접 구성할 것.
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client(monkeypatch: pytest.MonkeyPatch) -> AsyncClient:
    # 필수 env를 import 전 주입 (settings는 module-load 시점에 한 번 평가됨)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )

    # 이전 테스트에서 캐시된 settings 무효화
    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
