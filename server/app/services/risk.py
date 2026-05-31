from __future__ import annotations

import math

W_JEONSE = 0.5
W_ACCIDENT = 0.1
W_FLOOD = 0.2
W_HUG = 0.2


def compute_risk(
    jeonse_ratio: float | None,
    flood_risk: bool | None,
    flood_year: int | None,
    build_year: int | None,
    hug_accident_count: int,
) -> dict:
    # 전세가율 축
    if jeonse_ratio is None:
        jeonse_score = 100.0
    else:
        jeonse_score = max(0.0, min(100.0, (90 - jeonse_ratio) / 50 * 100))

    # 침수 축
    if not flood_risk:
        flood_score = 100.0
    else:
        flood_score = 40.0
        if flood_year is not None:
            flood_score -= 20.0

    # HUG 축
    hug_score = 100.0 if jeonse_ratio is None or jeonse_ratio <= 90 else 40.0

    # 사고 축 — log10 정규화
    accident_score = max(0.0, min(100.0, 100.0 - math.log10(max(1, hug_accident_count)) * 20))

    total_safe = round(
        jeonse_score * W_JEONSE
        + accident_score * W_ACCIDENT
        + flood_score * W_FLOOD
        + hug_score * W_HUG
    )
    risk_pct = 100 - total_safe

    if risk_pct <= 30:
        grade = "안전"
    elif risk_pct <= 60:
        grade = "주의"
    else:
        grade = "위험"

    factors = [
        {
            "name": "전세가율",
            "weight": W_JEONSE,
            "score": round(jeonse_score),
            "basis": f"jeonse_ratio={jeonse_ratio}",
        },
        {
            "name": "사고",
            "weight": W_ACCIDENT,
            "score": round(accident_score),
            "basis": f"hug_accident_count={hug_accident_count}",
        },
        {
            "name": "침수",
            "weight": W_FLOOD,
            "score": round(flood_score),
            "basis": f"flood_risk={flood_risk}, flood_year={flood_year}",
        },
        {
            "name": "HUG",
            "weight": W_HUG,
            "score": round(hug_score),
            "basis": f"jeonse_ratio={jeonse_ratio}",
        },
    ]

    return {
        "jeonse_score": round(jeonse_score),
        "accident_score": round(accident_score),
        "flood_score": round(flood_score),
        "hug_score": round(hug_score),
        "total_safe": total_safe,
        "risk_pct": risk_pct,
        "grade": grade,
        "factors": factors,
    }
