from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Environment
    ENVIRONMENT: str = "development"  # development | staging | production
    LOG_LEVEL: str = "INFO"

    # App server
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"

    # Domain DB (SQLAlchemy + asyncpg) — required, fail-fast
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800  # seconds; prevents stale idle connections
    DB_ECHO: bool = False  # SQL query logging (dev only; perf + privacy in prod)

    # Session
    SESSION_TTL_DAYS: int = 30

    # OpenAI
    OPENAI_API_KEY: SecretStr | None = None

    # Kakao
    kakao_rest_api_key: str

    # ODsay
    odsay_api_key: str
    odsay_referer: str
    RECOMMEND_NEAREST_K: int = 40
    ODSAY_MAX_CONCURRENCY: int = 5

    # LangSmith tracing (enabled by default; requires LANGSMITH_API_KEY to actually upload traces)
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_PROJECT: str | None = None
    LANGSMITH_API_KEY: SecretStr | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Lazy + cached Settings — testable (override via dependency_overrides or env)."""
    return Settings()  # type: ignore[call-arg]


# 기존 import 호환 유지. 새 코드는 가능하면 get_settings() 사용 권장.
settings = get_settings()
