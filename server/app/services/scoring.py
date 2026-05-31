from __future__ import annotations

import math

TIME_FULL_MIN = 20
SATISFY_DROP = 25
OVER_PENALTY = 1.5
OVER_FLOOR = 20
TRANSFER_PENALTY = 5
WALK_FREE_M = 500
WALK_PENALTY_PER_100 = 1.5

MAX_BY_CATEGORY: dict[str, int] = {
    "cafe": 250,
    "food": 800,
    "culture": 100,
    "park": 85,
    "subway": 5,
    "hospital": 500,
    "pharmacy": 30,
    "mart": 4,
}


def _cat_score(count: int, cat: str) -> float:
    ratio = count / MAX_BY_CATEGORY[cat]
    if ratio >= 1:
        return 100.0
    return math.sqrt(ratio) * 100

def score_work(total_min: int, max_min: int, transfers: int = 0, walk_m: int = 0) -> int:
    if total_min <= TIME_FULL_MIN:
        time_score: float = 100.0
    elif total_min <= max_min:
        time_score = 100.0 - (total_min - TIME_FULL_MIN) / (max_min - TIME_FULL_MIN) * SATISFY_DROP
    else:
        time_score = max(float(OVER_FLOOR), 75.0 - (total_min - max_min) * OVER_PENALTY)
    transfer_penalty = transfers * TRANSFER_PENALTY
    walk_penalty = max(0.0, (walk_m - WALK_FREE_M) / 100 * WALK_PENALTY_PER_100)
    return round(max(0.0, time_score - transfer_penalty - walk_penalty))


def _tag_score(metrics: dict, categories: list[str], is_inverse: bool) -> float:
    avg = sum(_cat_score(metrics.get(c, 0), c) for c in categories) / len(categories)
    return 100.0 - avg if is_inverse else avg


def score_life(
    metrics: dict,
    lifestyle_tags: list[str],
    tag_mapping: dict[str, dict] | None = None,
) -> float:
    if tag_mapping is None:
        _tag_categories: dict[str, list[str]] = {
            "활기형": ["cafe", "food", "culture"],
            "조용형": ["cafe", "food"],
            "야근형": ["food"],
            "주말활동": ["park", "culture"],
            "카페·식당": ["cafe", "food"],
            "대중교통": ["subway"],
            "반려동물": ["park"],
        }
        _inverse_tags: set[str] = {"조용형"}

        if not lifestyle_tags:
            total = sum(_cat_score(metrics.get(c, 0), c) for c in MAX_BY_CATEGORY)
            return min(100, max(0, round(total / len(MAX_BY_CATEGORY))))

        known_tags = [t for t in lifestyle_tags if t in _tag_categories]
        if not known_tags:
            return 0

        scores = [
            _tag_score(metrics, _tag_categories[tag], tag in _inverse_tags)
            for tag in known_tags
        ]
        return min(100, max(0, round(sum(scores) / len(scores))))

    if not lifestyle_tags:
        total = sum(_cat_score(metrics.get(c, 0), c) for c in MAX_BY_CATEGORY)
        return float(min(100.0, max(0.0, total / len(MAX_BY_CATEGORY))))

    known_tags = [t for t in lifestyle_tags if t in tag_mapping]
    if not known_tags:
        return 0.0

    scores_f = [
        _tag_score(
            metrics,
            tag_mapping[tag]["categories"],
            tag_mapping[tag].get("is_inverse", False),
        )
        for tag in known_tags
    ]
    return float(min(100.0, max(0.0, sum(scores_f) / len(scores_f))))


def score_safe(jeonse_ratio_avg: float, flood_ratio: float, avg_build_year: int) -> int:
    # 전세가율: 40% 이하=100, 90% 이상=0 선형 (낮을수록 깡통전세 위험 ↓)
    jeonse_score = max(0.0, min(100.0, (90 - jeonse_ratio_avg) / 50 * 100))

    # 침수 비율(0~1): 0%=100, 12.5% 이상=0 선형
    flood_score = max(0.0, 100 - flood_ratio * 100 * 8)

    # 노후도: 5년 이하=100, 40년 이상=0 선형
    age = 2026 - avg_build_year
    age_score = max(0.0, min(100.0, (40 - age) / 35 * 100))

    return round(0.5 * jeonse_score + 0.3 * flood_score + 0.2 * age_score)


def compute_total(scores: dict[str, int], priority: str | None) -> int:
    w_work, w_life, w_safe = 0.4, 0.3, 0.3
    if priority == "safety":
        w_work, w_life, w_safe = 0.3, 0.2, 0.5
    elif priority == "life":
        w_work, w_life, w_safe = 0.3, 0.5, 0.2
    return round(scores["work"] * w_work + scores["life"] * w_life + scores["safe"] * w_safe)
