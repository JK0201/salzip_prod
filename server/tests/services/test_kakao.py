import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_mock_client(status_code: int, documents: list) -> AsyncMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {"documents": documents}

    mock_client = AsyncMock()
    mock_client.get.return_value = response
    return mock_client


# acceptance #1
def test_geocode_address_importable_and_is_coroutine():
    from app.services.kakao import geocode_address

    assert inspect.iscoroutinefunction(geocode_address)


# acceptance #2
async def test_geocode_address_empty_string_returns_none():
    from app.services.kakao import geocode_address

    result = await geocode_address("")
    assert result is None


# acceptance #3
async def test_geocode_address_returns_lat_lng_tuple(monkeypatch):
    from app.core.config import settings
    from app.services.kakao import geocode_address

    monkeypatch.setattr(settings, "kakao_rest_api_key", "test-key")

    mock_client = _make_mock_client(200, [{"y": "37.5", "x": "127.0"}])
    result = await geocode_address("서울시 강남구", client=mock_client)
    assert result == (37.5, 127.0)


# acceptance #4
async def test_geocode_address_empty_documents_returns_none(monkeypatch):
    from app.core.config import settings
    from app.services.kakao import geocode_address

    monkeypatch.setattr(settings, "kakao_rest_api_key", "test-key")

    mock_client = _make_mock_client(200, [])
    result = await geocode_address("서울시 강남구", client=mock_client)
    assert result is None


# acceptance #5
async def test_geocode_address_status_500_returns_none(monkeypatch):
    from app.core.config import settings
    from app.services.kakao import geocode_address

    monkeypatch.setattr(settings, "kakao_rest_api_key", "test-key")

    mock_client = _make_mock_client(500, [{"y": "37.5", "x": "127.0"}])
    result = await geocode_address("서울시 강남구", client=mock_client)
    assert result is None


# acceptance #6
async def test_geocode_address_authorization_header_starts_with_kakao_ak(monkeypatch):
    from app.core.config import settings
    from app.services.kakao import geocode_address

    monkeypatch.setattr(settings, "kakao_rest_api_key", "test-key")

    mock_client = _make_mock_client(200, [{"y": "37.5", "x": "127.0"}])
    await geocode_address("서울시 강남구", client=mock_client)

    mock_client.get.assert_called_once()
    call_kwargs = mock_client.get.call_args.kwargs
    assert call_kwargs.get("headers", {}).get("Authorization", "").startswith("KakaoAK ")
