import typing
from pathlib import Path

import pytest

from app.core.config import Settings


# acceptance #1: SESSION_TTL_DAYS 필드 존재
def test_settings_has_session_ttl_days_field():
    assert "SESSION_TTL_DAYS" in Settings.model_fields


# acceptance #2: 타입 어노테이션이 int
def test_session_ttl_days_type_annotation_is_int():
    hints = typing.get_type_hints(Settings)
    assert hints["SESSION_TTL_DAYS"] is int


# acceptance #3 & #5: 기본값이 30
def test_session_ttl_days_default_is_30(monkeypatch):
    monkeypatch.delenv("SESSION_TTL_DAYS", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test/test")
    s = Settings()
    assert s.SESSION_TTL_DAYS == 30


# acceptance #4: .env.example에 SESSION_TTL_DAYS 키 라인 존재
def test_env_example_contains_session_ttl_days():
    content = Path(".env.example").read_text()
    lines_with_key = [ln for ln in content.splitlines() if "SESSION_TTL_DAYS" in ln]
    assert lines_with_key, ".env.example에 SESSION_TTL_DAYS 라인 없음"


# acceptance #6: 환경변수로 SESSION_TTL_DAYS 오버라이드 가능
def test_session_ttl_days_overridable_via_env(monkeypatch):
    monkeypatch.setenv("SESSION_TTL_DAYS", "7")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test/test")
    s = Settings()
    assert s.SESSION_TTL_DAYS == 7


# T-048: kakao/odsay 키 필드 -----------------------------------------------

# acceptance #1
def test_settings_has_kakao_rest_api_key_field():
    assert "kakao_rest_api_key" in Settings.model_fields


# acceptance #2
def test_settings_has_odsay_api_key_field():
    assert "odsay_api_key" in Settings.model_fields


# acceptance #3
def test_settings_has_odsay_referer_field():
    assert "odsay_referer" in Settings.model_fields


# acceptance #4
def test_new_api_key_fields_type_annotation_is_str():
    hints = typing.get_type_hints(Settings)
    assert hints["kakao_rest_api_key"] is str
    assert hints["odsay_api_key"] is str
    assert hints["odsay_referer"] is str


# acceptance #5
def test_new_api_key_fields_exposed_from_env(monkeypatch):
    monkeypatch.setenv("KAKAO_REST_API_KEY", "kakao-test-key")
    monkeypatch.setenv("ODSAY_API_KEY", "odsay-test-key")
    monkeypatch.setenv("ODSAY_REFERER", "http://localhost")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test/test")
    s = Settings()
    assert s.kakao_rest_api_key == "kakao-test-key"
    assert s.odsay_api_key == "odsay-test-key"
    assert s.odsay_referer == "http://localhost"


# acceptance #6
def test_existing_fields_not_removed():
    assert "DATABASE_URL" in Settings.model_fields
    assert "ENVIRONMENT" in Settings.model_fields
    assert "OPENAI_API_KEY" in Settings.model_fields


# T-131: nearest-K 설정 추가 --------------------------------------------------

_REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://test/test",
    "KAKAO_REST_API_KEY": "k",
    "ODSAY_API_KEY": "o",
    "ODSAY_REFERER": "http://localhost",
}


# acceptance #1: RECOMMEND_NEAREST_K 필드 존재, 기본값 40 (int)
def test_settings_has_recommend_nearest_k_field():
    assert "RECOMMEND_NEAREST_K" in Settings.model_fields


def test_recommend_nearest_k_type_is_int():
    hints = typing.get_type_hints(Settings)
    assert hints["RECOMMEND_NEAREST_K"] is int


def test_recommend_nearest_k_default_is_40(monkeypatch):
    for k, v in _REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("RECOMMEND_NEAREST_K", raising=False)
    s = Settings()
    assert s.RECOMMEND_NEAREST_K == 40


# acceptance #2: ODSAY_MAX_CONCURRENCY 필드 존재, 기본값 5 (int)
def test_settings_has_odsay_max_concurrency_field():
    assert "ODSAY_MAX_CONCURRENCY" in Settings.model_fields


def test_odsay_max_concurrency_type_is_int():
    hints = typing.get_type_hints(Settings)
    assert hints["ODSAY_MAX_CONCURRENCY"] is int


def test_odsay_max_concurrency_default_is_5(monkeypatch):
    for k, v in _REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("ODSAY_MAX_CONCURRENCY", raising=False)
    s = Settings()
    assert s.ODSAY_MAX_CONCURRENCY == 5


# acceptance #3: 기존 필드 기본값 회귀 없음
def test_existing_field_defaults_unchanged(monkeypatch):
    for k, v in _REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    s = Settings()
    assert s.APP_PORT == 8000
    assert s.DB_POOL_SIZE == 10
    assert s.DB_MAX_OVERFLOW == 20
    assert s.SESSION_TTL_DAYS == 30
