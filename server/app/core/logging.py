"""structlog + stdlib 통합 셋업.

- 외부 라이브러리(uvicorn, sqlalchemy, langchain) 로그도 root logger를 거쳐
  같은 ProcessorFormatter로 렌더링됨.
- 환경(ENVIRONMENT)에 따라 dev=ConsoleRenderer, 그 외=JSONRenderer.
"""

import logging
import sys

import structlog

from app.core.config import settings


def setup_logging() -> None:
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.dict_tracebacks,
    ]

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    renderer: structlog.types.Processor
    if settings.ENVIRONMENT == "development":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.LOG_LEVEL.upper())

    # 외부 라이브러리는 root로 propagate되도록 자체 handler 제거
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
        external = logging.getLogger(name)
        external.handlers = []
        external.propagate = True

    # 너무 시끄러운 access log는 별도로 레벨 낮춤
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
