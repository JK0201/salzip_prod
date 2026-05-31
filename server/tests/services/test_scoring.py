import ast
import inspect
import pathlib

import pytest
from app.services.scoring import score_work, score_life, score_safe, compute_total

# ---------- 공통 fixtures ----------

BASE_METRICS = {
    "cafe": 10,
    "food": 20,
    "culture": 5,
    "park": 8,
    "subway": 3,
    "hospital": 4,
    "pharmacy": 6,
    "mart": 7,
}


# ---------- score_work ----------


def test_score_work_within_cutoff():
    # B 룰셋: 15 <= TIME_FULL_MIN(20) → 만점
    assert score_work(15, 30) == 100


def test_score_work_exceeds_cutoff():
    # B 룰셋 초과식: max(20, 75 - (45-30)*1.5) = 52
    assert score_work(45, 30) == 52


def test_score_work_zero_commute():
    assert score_work(0, 30) == 100


# ---------- score_safe ----------


def test_score_safe_all_best():
    # 선형: jeonse 50→80, flood 0→100, age 6→97
    # 0.5*80 + 0.3*100 + 0.2*97.14 = 89
    assert score_safe(50.0, 0.0, 2020) == 89


def test_score_safe_all_worst():
    # 선형: jeonse 95→0, flood 0.15(15%)→0, age 46→0 = 0
    assert score_safe(95.0, 0.15, 1980) == 0


def test_score_safe_flood_ratio_scale():
    # flood_ratio는 0~1 비율. 침수 많을수록 점수 ↓
    base = score_safe(40.0, 0.0, 2020)
    flooded = score_safe(40.0, 0.05, 2020)  # 5%
    assert flooded < base


# ---------- compute_total ----------


def test_compute_total_priority_safety():
    # 80*0.3 + 70*0.2 + 60*0.5 = 24 + 14 + 30 = 68
    assert compute_total({"work": 80, "life": 70, "safe": 60}, "safety") == 68


def test_compute_total_priority_none():
    # 80*0.4 + 70*0.3 + 60*0.3 = 32 + 21 + 18 = 71
    assert compute_total({"work": 80, "life": 70, "safe": 60}, None) == 71


def test_compute_total_priority_empty_string():
    # 빈 문자열도 None과 동일 가중치
    assert compute_total({"work": 80, "life": 70, "safe": 60}, "") == 71


def test_compute_total_priority_life():
    expected = round(80 * 0.3 + 70 * 0.5 + 60 * 0.2)
    assert compute_total({"work": 80, "life": 70, "safe": 60}, "life") == expected


# ---------- score_life ----------


def test_score_life_vibrant_returns_int_in_range():
    result = score_life(BASE_METRICS, ["활기형"])
    assert isinstance(result, int)
    assert 0 <= result <= 100


def test_score_life_vibrant_only_cafe_food_culture_count():
    """활기형: 비관련 카테고리(park, subway, hospital, pharmacy, mart)만 증가해도 점수 불변"""
    non_vibrant_heavy = {**BASE_METRICS, "park": 999, "subway": 999, "hospital": 999, "pharmacy": 999, "mart": 999}
    assert score_life(BASE_METRICS, ["활기형"]) == score_life(non_vibrant_heavy, ["활기형"])


def test_score_life_vibrant_cafe_food_culture_affect_score():
    """cafe 증가 시 활기형 점수 변함"""
    higher = {**BASE_METRICS, "cafe": BASE_METRICS["cafe"] + 50}
    assert score_life(higher, ["활기형"]) != score_life(BASE_METRICS, ["활기형"])


def test_score_life_empty_tags_returns_int_in_range():
    result = score_life(BASE_METRICS, [])
    assert isinstance(result, int)
    assert 0 <= result <= 100


def test_score_life_empty_tags_all_categories_reflected():
    """빈 태그: MAX 미만 카테고리가 증가하면 점수 변해야 함.

    mart/subway처럼 MAX(4/5)가 작은 카테는 BASE 값이 이미 MAX 이상이면
    sqrt 정규화가 100으로 capped되어 불변 — 이는 정상(과포화).
    그래서 base를 MAX 미만 값으로 두고 소폭 증가로 검증.
    """
    from app.services.scoring import MAX_BY_CATEGORY

    low = {c: max(0, MAX_BY_CATEGORY[c] // 4) for c in MAX_BY_CATEGORY}
    base_score = score_life(low, [])
    for key in low:
        higher = {**low, key: low[key] + max(1, MAX_BY_CATEGORY[key] // 4)}
        assert score_life(higher, []) != base_score, f"{key} 증가해도 점수 불변 — 반영 안 됨"


def test_score_life_quiet_type_decreases_with_more_cafe_food():
    """조용형: cafe/food 카운트 클수록 점수 감소"""
    low_metrics = {**BASE_METRICS, "cafe": 5, "food": 5}
    high_metrics = {**BASE_METRICS, "cafe": 50, "food": 80}
    assert score_life(low_metrics, ["조용형"]) > score_life(high_metrics, ["조용형"])


def test_score_life_unknown_tag_returns_zero():
    assert score_life(BASE_METRICS, ["존재하지않는태그"]) == 0


# ---------- T-064: score_life DI 리팩터 ----------

SCORING_SRC = pathlib.Path("app/services/scoring.py")


def _module_level_names() -> set[str]:
    tree = ast.parse(SCORING_SRC.read_text())
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def test_no_module_level_tag_categories():
    assert "_TAG_CATEGORIES" not in _module_level_names()


def test_no_module_level_inverse_tags():
    assert "_INVERSE_TAGS" not in _module_level_names()


def test_score_life_signature_params():
    params = list(inspect.signature(score_life).parameters.keys())
    assert params == ["metrics", "lifestyle_tags", "tag_mapping"]


def test_score_life_with_tag_mapping_returns_positive():
    tag_mapping = {"식도락": {"categories": ["food"], "is_inverse": False}}
    result = score_life({"food": 10}, ["식도락"], tag_mapping)
    assert isinstance(result, float)
    assert result > 0


def test_score_life_unknown_tag_in_mapping_silent_skip():
    tag_mapping: dict = {}
    result = score_life({"food": 10}, ["존재안하는태그"], tag_mapping)
    assert isinstance(result, float)


def test_score_life_inverse_vs_non_inverse_differs():
    metrics = {"cafe": 30, "food": 40}
    tag_mapping_normal = {"태그A": {"categories": ["cafe", "food"], "is_inverse": False}}
    tag_mapping_inverse = {"태그A": {"categories": ["cafe", "food"], "is_inverse": True}}
    normal_score = score_life(metrics, ["태그A"], tag_mapping_normal)
    inverse_score = score_life(metrics, ["태그A"], tag_mapping_inverse)
    assert normal_score != inverse_score


def test_score_work_signature_unchanged():
    params = list(inspect.signature(score_work).parameters.keys())
    assert params == ["total_min", "max_min", "transfers", "walk_m"]


def test_score_safe_signature_unchanged():
    params = list(inspect.signature(score_safe).parameters.keys())
    assert params == ["jeonse_ratio_avg", "flood_ratio", "avg_build_year"]


def test_compute_total_signature_unchanged():
    params = list(inspect.signature(compute_total).parameters.keys())
    assert params == ["scores", "priority"]


# ---------- T-083: score_work B 룰셋 ----------
# NOTE: test_score_work_signature_unchanged(위)는 구 시그니처 ["commute_min","max_min"]를
#       assert → 새 acceptance #1과 충돌. coder가 해당 테스트 수정 필요.


def test_score_work_b_signature():
    # acceptance #1: 시그니처 (total_min, max_min, transfers=0, walk_m=0)
    params = list(inspect.signature(score_work).parameters.keys())
    assert params == ["total_min", "max_min", "transfers", "walk_m"]
    sig = inspect.signature(score_work)
    assert sig.parameters["transfers"].default == 0
    assert sig.parameters["walk_m"].default == 0


def test_score_work_b_full_score_walk_below_free():
    # acceptance #2: score_work(19, 45, 0, 493) == 100
    # 19 <= TIME_FULL_MIN(20) → time=100, walk_m 493<500 → no walk penalty
    assert score_work(19, 45, 0, 493) == 100


def test_score_work_b_heavy_penalty_clamps_to_zero():
    # acceptance #3: score_work(90, 45, 4, 2000) == 0
    # time: 90>45 → max(20, 75-(90-45)*1.5)=max(20,7.5)=20
    # transfer: 4*5=20, walk: (2000-500)/100*1.5=22.5 → 20-20-22.5=-22.5 → 0
    assert score_work(90, 45, 4, 2000) == 0


def test_score_work_b_transfer_penalty_reduces_score():
    # acceptance #4: score_work(30,45,0,0) > score_work(30,45,2,0)
    assert score_work(30, 45, 0, 0) > score_work(30, 45, 2, 0)


def test_score_work_b_walk_at_or_below_free_zone_no_penalty():
    # acceptance #5: score_work(30,45,0,400) == score_work(30,45,0,500)
    # 400 < WALK_FREE_M(500), 500 == WALK_FREE_M → both penalty=0
    assert score_work(30, 45, 0, 400) == score_work(30, 45, 0, 500)


def test_score_work_b_walk_above_free_zone_penalizes():
    # acceptance #6: score_work(30,45,0,800) < score_work(30,45,0,500)
    # (800-500)/100*1.5 = 4.5 penalty
    assert score_work(30, 45, 0, 800) < score_work(30, 45, 0, 500)


def test_score_work_b_two_arg_call_uses_defaults():
    # acceptance #7: score_work(30,45) transfers/walk_m 기본값 0으로 정상 동작
    result_explicit = score_work(30, 45, 0, 0)
    result_defaults = score_work(30, 45)
    assert result_explicit == result_defaults
    assert isinstance(result_defaults, int)
    assert 0 <= result_defaults <= 100


# ---------- T-091: MAX 현실화 + sqrt 헬퍼 ----------

SCORING_SRC_PATH = pathlib.Path("app/services/scoring.py")


def _has_import_math() -> bool:
    tree = ast.parse(SCORING_SRC_PATH.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "math":
                    return True
    return False


def test_scoring_has_import_math():
    assert _has_import_math(), "app/services/scoring.py에 `import math` 없음"


def test_max_by_category_food_cafe_culture_park():
    from app.services.scoring import MAX_BY_CATEGORY
    assert MAX_BY_CATEGORY["food"] == 800
    assert MAX_BY_CATEGORY["cafe"] == 250
    assert MAX_BY_CATEGORY["culture"] == 100
    assert MAX_BY_CATEGORY["park"] == 85


def test_max_by_category_subway_hospital_pharmacy_mart():
    from app.services.scoring import MAX_BY_CATEGORY
    assert MAX_BY_CATEGORY["subway"] == 5
    assert MAX_BY_CATEGORY["hospital"] == 500
    assert MAX_BY_CATEGORY["pharmacy"] == 30
    assert MAX_BY_CATEGORY["mart"] == 4


def test_cat_score_is_callable():
    from app.services.scoring import _cat_score
    assert callable(_cat_score)


def test_cat_score_normal_returns_sqrt_ratio():
    from app.services.scoring import _cat_score
    # sqrt(200/800)*100 = sqrt(0.25)*100 = 0.5*100 = 50.0
    assert _cat_score(200, "food") == 50.0


def test_cat_score_at_max_capped_to_100():
    from app.services.scoring import _cat_score
    # ratio == 1 → 100.0
    assert _cat_score(800, "food") == 100.0


def test_cat_score_over_max_capped_to_100():
    from app.services.scoring import _cat_score
    # ratio > 1 → 100.0
    assert _cat_score(1348, "food") == 100.0


def test_cat_score_small_value_approx():
    from app.services.scoring import _cat_score
    # sqrt(50/800)*100 ≈ 25.0
    result = _cat_score(50, "food")
    assert abs(result - 25.0) < 0.5


# ---------- T-092: score_life sqrt 재작성 ----------


def test_score_life_empty_tags_uses_cat_score_avg():
    # acceptance #1: 빈 태그 → sum(_cat_score(c)) / 8
    # old: sum(raw_ratio)/8*100 → 35, new: sum(sqrt_ratio)/8 → ~40
    from app.services.scoring import _cat_score, MAX_BY_CATEGORY
    expected = sum(_cat_score(BASE_METRICS.get(c, 0), c) for c in MAX_BY_CATEGORY) / len(MAX_BY_CATEGORY)
    result = score_life(BASE_METRICS, [], tag_mapping=None)
    assert abs(result - expected) < 1


def test_score_life_single_food_tag_at_max_returns_near_100():
    # acceptance #2: food=800(MAX) → >=99
    tag_mapping = {"식도락형": {"categories": ["food"], "is_inverse": False}}
    result = score_life({"food": 800}, ["식도락형"], tag_mapping)
    assert result >= 99


def test_score_life_two_tags_returns_average_of_cat_scores():
    # acceptance #3: 2 태그 → 두 태그 점수의 평균
    # old: (200/800*100 + 100/250*100)/2 = (25+40)/2 = 32.5
    # new: (_cat_score(200,"food") + _cat_score(100,"cafe"))/2 = (50+63.2)/2 ≈ 56.6
    from app.services.scoring import _cat_score
    tag_mapping = {
        "태그A": {"categories": ["food"], "is_inverse": False},
        "태그B": {"categories": ["cafe"], "is_inverse": False},
    }
    metrics = {"food": 200, "cafe": 100}
    expected = (_cat_score(200, "food") + _cat_score(100, "cafe")) / 2
    result = score_life(metrics, ["태그A", "태그B"], tag_mapping)
    assert abs(result - expected) < 1


def test_score_life_inverse_subway_decreases_with_more_count():
    # acceptance #4: subway 카운트 클수록 점수 낮아짐
    tag_mapping = {"대중교통형": {"categories": ["subway"], "is_inverse": True}}
    low = score_life({"subway": 1}, ["대중교통형"], tag_mapping)
    high = score_life({"subway": 4}, ["대중교통형"], tag_mapping)
    assert high < low


def test_score_life_inverse_tag_formula_is_100_minus_cat_score():
    # acceptance #4: inverse = 100 - _cat_score (not (MAX-val)/MAX*100)
    # subway=4: old=(5-4)/5*100=20, new=100-sqrt(4/5)*100≈10.6
    from app.services.scoring import _cat_score
    tag_mapping = {"대중교통형": {"categories": ["subway"], "is_inverse": True}}
    result = score_life({"subway": 4}, ["대중교통형"], tag_mapping)
    expected = 100 - _cat_score(4, "subway")
    assert abs(result - expected) < 1


def test_score_life_two_category_tag_averages_cat_scores():
    # acceptance #5: hospital+pharmacy → 두 _cat_score의 평균
    # old: (250+15)/(500+30)*100 = 50.0
    # new: (_cat_score(250,"hospital") + _cat_score(15,"pharmacy"))/2 ≈ 70.7
    from app.services.scoring import _cat_score
    tag_mapping = {"건강형": {"categories": ["hospital", "pharmacy"], "is_inverse": False}}
    metrics = {"hospital": 250, "pharmacy": 15}
    expected = (_cat_score(250, "hospital") + _cat_score(15, "pharmacy")) / 2
    result = score_life(metrics, ["건강형"], tag_mapping)
    assert abs(result - expected) < 1


@pytest.mark.parametrize("metrics,tags,tag_mapping", [
    ({"food": 999999}, ["식도락형"], {"식도락형": {"categories": ["food"], "is_inverse": False}}),
    ({"subway": 0}, ["대중교통형"], {"대중교통형": {"categories": ["subway"], "is_inverse": True}}),
    ({}, [], None),
    ({"food": 800, "cafe": 250}, [], None),
])
def test_score_life_returns_in_0_100_range(metrics, tags, tag_mapping):
    # acceptance #6: 모든 반환값 0~100 clamp
    result = score_life(metrics, tags, tag_mapping)
    assert 0 <= result <= 100


def test_score_life_t092_signature_and_unknown_tag_returns_zero():
    # acceptance #7: 시그니처 유지, known 태그 없으면 0
    import inspect
    params = list(inspect.signature(score_life).parameters.keys())
    assert params == ["metrics", "lifestyle_tags", "tag_mapping"]
    result = score_life({"food": 100}, ["없는태그"], {})
    assert result == 0
