from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1 import job_categories as job_categories_router
from app.api.v1 import lifestyle_tags as lifestyle_tags_router
from app.api.v1 import policies_eligible as policies_eligible_router
from app.api.v1 import policies_preview as policies_preview_router
from app.api.v1.router import router as v1_router
from app.core.checkpointer import lifespan_checkpointer
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.db.session import create_db_engine

# 로깅은 가능한 한 일찍 셋업 — module-level logger 캐시(`cache_logger_on_first_use=True`)
# 가 잘못된 핸들러로 굳지 않도록.
setup_logging()
log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("startup", environment=settings.ENVIRONMENT)
    engine = create_db_engine()
    app.state.engine = engine
    try:
        async with lifespan_checkpointer() as checkpointer:
            app.state.checkpointer = checkpointer
            yield
    finally:
        await engine.dispose()
        log.info("shutdown")


app = FastAPI(
    title="template",
    description="template",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware (GZip 먼저 → 응답 압축, CORS는 가장 바깥)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # production: 도메인 명시
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(v1_router, prefix="/api/v1")
app.include_router(job_categories_router.router, prefix="/api/v1")
app.include_router(lifestyle_tags_router.router, prefix="/api/v1")
app.include_router(policies_preview_router.router, prefix="/api/v1")
app.include_router(policies_eligible_router.router, prefix="/api/v1")


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
