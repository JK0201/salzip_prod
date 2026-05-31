import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


ORIGIN = (37.1234, 127.5678)
DEST = (37.9999, 127.0001)
AREA_ID = uuid.uuid4()


def _make_cache_row(total_time_min=30, payment_won=1500, first_lane="2호선"):
    row = MagicMock()
    row.total_time_min = total_time_min
    row.payment_won = payment_won
    row.first_lane = first_lane
    return row


def _make_cache_row_full(
    total_time_min=30, payment_won=1500, first_lane="2호선", transfers=2, total_walk_m=400
):
    row = MagicMock()
    row.total_time_min = total_time_min
    row.payment_won = payment_won
    row.first_lane = first_lane
    row.transfers = transfers
    row.total_walk_m = total_walk_m
    return row


def _success_body_with_transit(
    total_time=25,
    payment=1450,
    bus_transit=1,
    subway_transit=2,
    total_walk=600,
    lane_name="3호선",
):
    return {
        "result": {
            "path": [
                {
                    "info": {
                        "totalTime": total_time,
                        "payment": payment,
                        "busTransitCount": bus_transit,
                        "subwayTransitCount": subway_transit,
                        "totalWalk": total_walk,
                    },
                    "subPath": [
                        {"trafficType": 1, "lane": [{"name": lane_name}]}
                    ],
                }
            ]
        }
    }


def _make_conn(row):
    conn = AsyncMock()
    result = MagicMock()
    result.first.return_value = row
    conn.execute.return_value = result
    return conn


def _make_mock_client(status_code: int, body: dict) -> AsyncMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body
    mock_client = AsyncMock()
    mock_client.get.return_value = response
    return mock_client


def _success_body():
    return {
        "result": {
            "path": [
                {
                    "info": {"totalTime": 25, "payment": 1450},
                    "subPath": [
                        {"trafficType": 1, "lane": [{"name": "3호선"}]}
                    ],
                }
            ]
        }
    }


# acceptance #1
def test_transit_time_importable_and_is_coroutine():
    from app.services.odsay import transit_time

    assert inspect.iscoroutinefunction(transit_time)


# acceptance #2
async def test_transit_time_cache_hit_returns_row_without_http_call(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")

    row = _make_cache_row(total_time_min=30, payment_won=1500, first_lane="2호선")
    conn = _make_conn(row)
    mock_client = AsyncMock()

    result = await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    assert result == {"min": 30, "payment": 1500, "first_lane": "2호선"}
    mock_client.get.assert_not_called()


# acceptance #3
async def test_transit_time_cache_miss_returns_api_result(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")
    monkeypatch.setattr(settings, "odsay_referer", "https://example.com")

    conn = _make_conn(None)
    mock_client = _make_mock_client(200, _success_body())

    result = await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    assert result == {"min": 25, "payment": 1450, "first_lane": "3호선"}


# acceptance #4
async def test_transit_time_cache_miss_calls_get_once_with_correct_referer(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")
    monkeypatch.setattr(settings, "odsay_referer", "https://test-referer.com")

    conn = _make_conn(None)
    mock_client = _make_mock_client(200, _success_body())

    await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    mock_client.get.assert_called_once()
    call_kwargs = mock_client.get.call_args.kwargs
    assert call_kwargs.get("headers", {}).get("Referer") == "https://test-referer.com"


# acceptance #5
async def test_transit_time_cache_miss_success_executes_insert(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time
    from sqlalchemy.sql.dml import Insert

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")
    monkeypatch.setattr(settings, "odsay_referer", "https://example.com")

    conn = _make_conn(None)
    mock_client = _make_mock_client(200, _success_body())

    await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    insert_calls = [
        c for c in conn.execute.call_args_list if isinstance(c.args[0], Insert)
    ]
    assert len(insert_calls) == 1


# acceptance #6
async def test_transit_time_no_result_key_returns_none_without_insert(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time
    from sqlalchemy.sql.dml import Insert

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")
    monkeypatch.setattr(settings, "odsay_referer", "https://example.com")

    conn = _make_conn(None)
    mock_client = _make_mock_client(200, {"no_result_key": True})

    result = await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    assert result is None
    insert_calls = [
        c for c in conn.execute.call_args_list if isinstance(c.args[0], Insert)
    ]
    assert len(insert_calls) == 0


# acceptance #7
async def test_transit_time_status_500_returns_none_without_insert(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time
    from sqlalchemy.sql.dml import Insert

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")
    monkeypatch.setattr(settings, "odsay_referer", "https://example.com")

    conn = _make_conn(None)
    mock_client = _make_mock_client(500, _success_body())

    result = await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    assert result is None
    insert_calls = [
        c for c in conn.execute.call_args_list if isinstance(c.args[0], Insert)
    ]
    assert len(insert_calls) == 0


# T-084 acceptance #1: miss 경로 transfers == busTransitCount + subwayTransitCount
async def test_transit_time_miss_transfers_equals_bus_plus_subway(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")
    monkeypatch.setattr(settings, "odsay_referer", "https://example.com")

    conn = _make_conn(None)
    mock_client = _make_mock_client(200, _success_body_with_transit(bus_transit=1, subway_transit=2))

    result = await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    assert result is not None
    assert result["transfers"] == 3  # 1 + 2


# T-084 acceptance #2: miss 경로 total_walk_m == totalWalk
async def test_transit_time_miss_total_walk_m_equals_totalWalk(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")
    monkeypatch.setattr(settings, "odsay_referer", "https://example.com")

    conn = _make_conn(None)
    mock_client = _make_mock_client(200, _success_body_with_transit(total_walk=850))

    result = await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    assert result is not None
    assert result["total_walk_m"] == 850


# T-084 acceptance #3: cache hit 반환 dict에 transfers 키 포함 (row 값)
async def test_transit_time_cache_hit_includes_transfers(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")

    row = _make_cache_row_full(transfers=3)
    conn = _make_conn(row)
    mock_client = AsyncMock()

    result = await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    assert result is not None
    assert "transfers" in result
    assert result["transfers"] == 3


# T-084 acceptance #4: cache hit 반환 dict에 total_walk_m 키 포함 (row 값)
async def test_transit_time_cache_hit_includes_total_walk_m(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")

    row = _make_cache_row_full(total_walk_m=720)
    conn = _make_conn(row)
    mock_client = AsyncMock()

    result = await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    assert result is not None
    assert "total_walk_m" in result
    assert result["total_walk_m"] == 720


# T-084 acceptance #5: info에 키 없을 때 transfers=0, total_walk_m=0
async def test_transit_time_miss_missing_transit_keys_defaults_to_zero(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")
    monkeypatch.setattr(settings, "odsay_referer", "https://example.com")

    body = {
        "result": {
            "path": [
                {
                    "info": {"totalTime": 20, "payment": 1000},
                    "subPath": [
                        {"trafficType": 1, "lane": [{"name": "1호선"}]}
                    ],
                }
            ]
        }
    }
    conn = _make_conn(None)
    mock_client = _make_mock_client(200, body)

    result = await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    assert result is not None
    assert result["transfers"] == 0
    assert result["total_walk_m"] == 0


# T-084 acceptance #6: 반환 dict에 기존 min, payment, first_lane 키 유지됨 (miss 경로)
async def test_transit_time_miss_preserves_existing_keys(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")
    monkeypatch.setattr(settings, "odsay_referer", "https://example.com")

    conn = _make_conn(None)
    mock_client = _make_mock_client(
        200, _success_body_with_transit(total_time=30, payment=1300, lane_name="신분당선")
    )

    result = await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    assert result is not None
    assert result["min"] == 30
    assert result["payment"] == 1300
    assert result["first_lane"] == "신분당선"


# T-084 acceptance #6: 반환 dict에 기존 min, payment, first_lane 키 유지됨 (cache hit 경로)
async def test_transit_time_cache_hit_preserves_existing_keys(monkeypatch):
    from app.core.config import settings
    from app.services.odsay import transit_time

    monkeypatch.setattr(settings, "odsay_api_key", "test-key")

    row = _make_cache_row_full(total_time_min=45, payment_won=1800, first_lane="9호선")
    conn = _make_conn(row)
    mock_client = AsyncMock()

    result = await transit_time(ORIGIN, AREA_ID, DEST, conn, client=mock_client)

    assert result is not None
    assert result["min"] == 45
    assert result["payment"] == 1800
    assert result["first_lane"] == "9호선"
