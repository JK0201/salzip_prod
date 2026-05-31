import math
from pathlib import Path

import pytest

import app.services.risk as risk_module
from app.services.risk import compute_risk


# acceptance #1: accident_score == 100 when hug_accident_count=1
def test_accident_score_is_100_when_count_1():
    result = compute_risk(
        jeonse_ratio=50,
        flood_risk=False,
        flood_year=None,
        build_year=2010,
        hug_accident_count=1,
    )
    assert result["accident_score"] == pytest.approx(100.0)


# acceptance #2: accident_score ≈ 60 (±1) when hug_accident_count=100
def test_accident_score_is_60_when_count_100():
    result = compute_risk(
        jeonse_ratio=50,
        flood_risk=False,
        flood_year=None,
        build_year=2010,
        hug_accident_count=100,
    )
    assert abs(result["accident_score"] - 60.0) <= 1.0


# acceptance #3: accident_score ≈ 20 (±1) when hug_accident_count=10000
def test_accident_score_is_20_when_count_10000():
    result = compute_risk(
        jeonse_ratio=50,
        flood_risk=False,
        flood_year=None,
        build_year=2010,
        hug_accident_count=10000,
    )
    assert abs(result["accident_score"] - 20.0) <= 1.0


# acceptance #4: accident_score == 0 when hug_accident_count=100000
def test_accident_score_is_0_when_count_100000():
    result = compute_risk(
        jeonse_ratio=50,
        flood_risk=False,
        flood_year=None,
        build_year=2010,
        hug_accident_count=100000,
    )
    assert result["accident_score"] == pytest.approx(0.0)


# acceptance #5: weight constants W_JEONSE=0.5, W_ACCIDENT=0.1, W_FLOOD=0.2, W_HUG=0.2, sum=1.0
def test_weight_constants_values_and_sum():
    assert risk_module.W_JEONSE == pytest.approx(0.5)
    assert risk_module.W_ACCIDENT == pytest.approx(0.1)
    assert risk_module.W_FLOOD == pytest.approx(0.2)
    assert risk_module.W_HUG == pytest.approx(0.2)
    total = risk_module.W_JEONSE + risk_module.W_ACCIDENT + risk_module.W_FLOOD + risk_module.W_HUG
    assert total == pytest.approx(1.0)


# acceptance #6: all required keys present in return dict (regression)
def test_compute_risk_returns_all_required_keys():
    result = compute_risk(
        jeonse_ratio=50,
        flood_risk=False,
        flood_year=None,
        build_year=2010,
        hug_accident_count=1,
    )
    for key in ("jeonse_score", "accident_score", "flood_score", "hug_score", "total_safe", "risk_pct", "grade", "factors"):
        assert key in result, f"missing key: {key}"


# acceptance #7: factors weights match new constants per axis name
def test_factors_weights_match_new_constants():
    result = compute_risk(
        jeonse_ratio=50,
        flood_risk=False,
        flood_year=None,
        build_year=2010,
        hug_accident_count=1,
    )
    factors = result["factors"]
    by_name = {f["name"]: f["weight"] for f in factors}
    assert by_name["전세가율"] == pytest.approx(0.5)
    assert by_name["사고"] == pytest.approx(0.1)
    assert by_name["침수"] == pytest.approx(0.2)
    assert by_name["HUG"] == pytest.approx(0.2)


# acceptance #8: grade boundary — safe ≤30, caution ≤60, danger >60
@pytest.mark.parametrize("jeonse_ratio,flood_risk,flood_year,build_year,hug_accident_count,expected_grade", [
    (20.0, False, None, 2020, 1, "안전"),
    (75.0, False, None, 2010, 1, "주의"),
    (95.0, True, 2022, None, 10000, "위험"),
])
def test_grade_boundary(jeonse_ratio, flood_risk, flood_year, build_year, hug_accident_count, expected_grade):
    result = compute_risk(
        jeonse_ratio=jeonse_ratio,
        flood_risk=flood_risk,
        flood_year=flood_year,
        build_year=build_year,
        hug_accident_count=hug_accident_count,
    )
    rp = result["risk_pct"]
    grade = result["grade"]
    # verify grade string matches risk_pct boundary logic
    if rp <= 30:
        assert grade == "안전", f"risk_pct={rp} should be 안전, got {grade}"
    elif rp <= 60:
        assert grade == "주의", f"risk_pct={rp} should be 주의, got {grade}"
    else:
        assert grade == "위험", f"risk_pct={rp} should be 위험, got {grade}"
    assert grade == expected_grade, f"expected {expected_grade} for inputs, got {grade} (risk_pct={rp})"


# acceptance #9: compute_risk(None, None, None, None, 0) returns dict with risk_pct in 0~100 (regression)
def test_all_none_inputs_returns_valid_dict():
    result = compute_risk(
        jeonse_ratio=None,
        flood_risk=None,
        flood_year=None,
        build_year=None,
        hug_accident_count=0,
    )
    assert isinstance(result, dict)
    assert "risk_pct" in result
    assert 0 <= result["risk_pct"] <= 100


# acceptance #10: docs/spec_norm.md §3-2 table updated to new weights
def test_spec_norm_md_section_3_2_weights_updated():
    content = Path("docs/spec_norm.md").read_text()
    assert "| 전세가율 | 0.5 |" in content, "spec_norm.md §3-2: 전세가율 weight should be 0.5"
    assert "| 유형 사고율 | 0.1 |" in content, "spec_norm.md §3-2: 유형 사고율 weight should be 0.1"
    assert "| 침수 위험 | 0.2 |" in content, "spec_norm.md §3-2: 침수 위험 weight should be 0.2 (unchanged)"
    assert "| HUG 보증 가능 | 0.2 |" in content, "spec_norm.md §3-2: HUG 보증 가능 weight should be 0.2 (unchanged)"
    # old weights must not appear in the 4-axis table
    assert "| 전세가율 | 0.4 |" not in content, "spec_norm.md §3-2: old weight 0.4 for 전세가율 must be removed"
    assert "| 유형 사고율 | 0.2 |" not in content, "spec_norm.md §3-2: old weight 0.2 for 사고율 must be removed"
