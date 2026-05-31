from decimal import Decimal

import pytest

from app.services.reb_trend import compute_market_trend


# ── acceptance #1 ──────────────────────────────────────────────────────────────
def test_returns_latest_and_direction_keys_per_metric():
    series = {
        "price": [("2024-01", 100.0), ("2024-02", 110.0)],
        "volume": [("2024-01", 50.0), ("2024-02", 45.0)],
    }
    result = compute_market_trend(series)

    assert "price" in result
    assert "volume" in result
    assert "latest" in result["price"]
    assert "direction" in result["price"]
    assert "latest" in result["volume"]
    assert "direction" in result["volume"]
    assert "summary" in result


# ── acceptance #2 ──────────────────────────────────────────────────────────────
def test_direction_increases_when_over_5pct():
    # (110 - 100) / 100 = 0.10 > 0.05 → 증가
    series = {"price": [("2024-01", 100.0), ("2024-02", 110.0)]}
    result = compute_market_trend(series)

    assert result["price"]["direction"] == "증가"
    assert result["price"]["latest"] == pytest.approx(110.0)


def test_direction_increases_boundary_just_over_5pct():
    # (105.1 - 100) / 100 = 0.051 → 증가
    series = {"price": [("2024-01", 100.0), ("2024-02", 105.1)]}
    result = compute_market_trend(series)

    assert result["price"]["direction"] == "증가"


# ── acceptance #3 ──────────────────────────────────────────────────────────────
def test_direction_decreases_when_over_5pct_negative():
    # (90 - 100) / 100 = -0.10 < -0.05 → 감소
    series = {"price": [("2024-01", 100.0), ("2024-02", 90.0)]}
    result = compute_market_trend(series)

    assert result["price"]["direction"] == "감소"
    assert result["price"]["latest"] == pytest.approx(90.0)


def test_direction_decreases_boundary_just_under_neg_5pct():
    # (94.9 - 100) / 100 = -0.051 → 감소
    series = {"price": [("2024-01", 100.0), ("2024-02", 94.9)]}
    result = compute_market_trend(series)

    assert result["price"]["direction"] == "감소"


# ── acceptance #4 ──────────────────────────────────────────────────────────────
def test_direction_stable_within_5pct():
    # (102 - 100) / 100 = 0.02 → 유지
    series = {"price": [("2024-01", 100.0), ("2024-02", 102.0)]}
    result = compute_market_trend(series)

    assert result["price"]["direction"] == "유지"


def test_direction_stable_exactly_at_boundary():
    # (105 - 100) / 100 = 0.05 → ±5% 이내(경계 포함) → 유지
    series = {"price": [("2024-01", 100.0), ("2024-02", 105.0)]}
    result = compute_market_trend(series)

    assert result["price"]["direction"] == "유지"


def test_direction_stable_negative_boundary():
    # (95 - 100) / 100 = -0.05 → 유지
    series = {"price": [("2024-01", 100.0), ("2024-02", 95.0)]}
    result = compute_market_trend(series)

    assert result["price"]["direction"] == "유지"


# ── acceptance #5 ──────────────────────────────────────────────────────────────
def test_empty_list_returns_none_and_nothing_no_exception():
    series = {"price": []}
    result = compute_market_trend(series)

    assert result["price"]["latest"] is None
    assert result["price"]["direction"] == "없음"


def test_all_none_values_returns_none_and_nothing_no_exception():
    series = {"price": [("2024-01", None), ("2024-02", None), ("2024-03", None)]}
    result = compute_market_trend(series)

    assert result["price"]["latest"] is None
    assert result["price"]["direction"] == "없음"


# ── acceptance #6 ──────────────────────────────────────────────────────────────
def test_single_valid_value_latest_filled_direction_nothing():
    series = {"price": [("2024-01", 200.0)]}
    result = compute_market_trend(series)

    assert result["price"]["latest"] == pytest.approx(200.0)
    assert result["price"]["direction"] == "없음"


def test_single_valid_value_among_nones_direction_nothing():
    # None 앞뒤로 둘러싸인 유효값 1개
    series = {"price": [("2024-01", None), ("2024-02", 150.0), ("2024-03", None)]}
    result = compute_market_trend(series)

    assert result["price"]["latest"] == pytest.approx(150.0)
    assert result["price"]["direction"] == "없음"


# ── acceptance #7 ──────────────────────────────────────────────────────────────
def test_summary_contains_역전세_when_unsold_up_tx_down():
    # unsold 증가(+10%) + apt_tx_monthly 감소(-10%) → summary에 '역전세'
    series = {
        "unsold": [("2024-01", 100.0), ("2024-02", 110.0)],
        "apt_tx_monthly": [("2024-01", 500.0), ("2024-02", 450.0)],
    }
    result = compute_market_trend(series)

    assert "역전세" in result["summary"]


def test_summary_no_역전세_when_both_increase():
    # unsold 증가 + apt_tx_monthly 증가 → '역전세' 없음
    series = {
        "unsold": [("2024-01", 100.0), ("2024-02", 120.0)],
        "apt_tx_monthly": [("2024-01", 500.0), ("2024-02", 600.0)],
    }
    result = compute_market_trend(series)

    assert "역전세" not in result["summary"]


def test_summary_no_역전세_when_only_unsold_up():
    # unsold 증가지만 apt_tx_monthly 증가 → '역전세' 없음
    series = {
        "unsold": [("2024-01", 100.0), ("2024-02", 120.0)],
        "apt_tx_monthly": [("2024-01", 500.0), ("2024-02", 510.0)],
    }
    result = compute_market_trend(series)

    assert "역전세" not in result["summary"]


# ── 스펙 명시 엣지 케이스 ───────────────────────────────────────────────────────
def test_earliest_zero_no_division_error():
    # earliest == 0 → ZeroDivisionError 없이 안전 처리
    series = {"price": [("2024-01", 0.0), ("2024-02", 100.0)]}
    result = compute_market_trend(series)

    assert result["price"]["direction"] in ("유지", "없음")
    assert result["price"]["latest"] == pytest.approx(100.0)


def test_none_values_skipped_latest_is_last_nonone():
    # None 혼재 → 마지막 non-None이 latest
    series = {"price": [("2024-01", 100.0), ("2024-02", None), ("2024-03", 130.0), ("2024-04", None)]}
    result = compute_market_trend(series)

    assert result["price"]["latest"] == pytest.approx(130.0)


def test_decimal_values_accepted_no_exception():
    # Decimal 타입 허용 확인
    series = {"price": [("2024-01", Decimal("100")), ("2024-02", Decimal("120"))]}
    result = compute_market_trend(series)

    assert result["price"]["direction"] == "증가"
    assert isinstance(result["price"]["latest"], float)


def test_latest_is_returned_as_float():
    # spec: latest는 float으로 채운다
    series = {"price": [("2024-01", 100), ("2024-02", 110)]}  # int 입력
    result = compute_market_trend(series)

    assert isinstance(result["price"]["latest"], float)
