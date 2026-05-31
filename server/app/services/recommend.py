from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

import httpx
import sqlalchemy as sa
import structlog
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import AddressNotFound
from app.db.tables.lifestyle_tags import lifestyle_tags_table
from app.services import kakao, odsay, scoring
from app.utils import geo

logger = structlog.get_logger(__name__)

_DEFAULT_LISTING: dict[str, Any] = {
    "jeonse_ratio_avg": 0,
    "flood_ratio": 0,
    "avg_build_year": 2026,
    "listing_count": 0,
    "flood_risk_count": 0,
}


async def recommend(req, conn, session_id: uuid.UUID | None = None) -> list[dict] | dict:
    coords = await kakao.geocode_address(req.workplace_address)
    if coords is None:
        raise AddressNotFound("address_not_found")

    area_result = await conn.execute(
        text("""
            SELECT a.id AS area_id, a.emd_name, a.lat, a.lng, r.sgg_name
            FROM areas a
            JOIN regions r ON r.id = a.region_id
            WHERE a.lat IS NOT NULL AND a.lng IS NOT NULL
        """)
    )
    area_rows = area_result.fetchall()
    area_rows = sorted(
        area_rows,
        key=lambda r: geo.haversine_km(coords[0], coords[1], float(r.lat), float(r.lng)),
    )[: settings.RECOMMEND_NEAREST_K]

    cache = await odsay.load_cache_batch(coords, [row.area_id for row in area_rows], conn)
    miss_rows = [row for row in area_rows if row.area_id not in cache]
    if miss_rows:
        sem = asyncio.Semaphore(settings.ODSAY_MAX_CONCURRENCY)
        async with httpx.AsyncClient() as http:

            async def _fetch_one(row):
                async with sem:
                    return await odsay.transit_time(
                        coords, row.area_id, (float(row.lat), float(row.lng)), conn, client=http
                    )

            fetched = await asyncio.gather(*[_fetch_one(row) for row in miss_rows])
        for row, result in zip(miss_rows, fetched, strict=False):
            if result is not None:
                cache[row.area_id] = result
    transit_results = [cache.get(row.area_id) for row in area_rows]

    candidates = []
    for row, transit in zip(area_rows, transit_results, strict=False):
        if transit is None:
            continue
        if transit["min"] > req.max_commute_minutes:
            continue
        candidates.append((row, transit))

    if not candidates:
        return []

    area_ids = [row.area_id for row, _ in candidates]

    metrics_result = await conn.execute(
        text("""
            SELECT
                area_id,
                cafe_count,
                food_count,
                culture_count,
                park_count,
                mart_count,
                subway_count,
                hospital_count,
                pharmacy_count,
                avg_jeonse_ratio,
                flood_ratio,
                avg_build_year,
                listing_count,
                flood_risk_count
            FROM area_metrics
            WHERE area_id = ANY(:area_ids)
        """).bindparams(area_ids=area_ids)
    )
    metrics_rows = metrics_result.mappings().all()
    metrics_by_id = {row.area_id: row for row in metrics_rows}

    # T-077 format: area_metrics has pre-computed aggregate columns (cafe_count etc.)
    # Legacy format: area_metrics has short aliases (cafe, food, ...) via old SQL
    _sample = next(iter(metrics_by_id.values()), None)
    _t077 = _sample is not None and hasattr(_sample, "cafe_count")

    if _t077:
        listing_by_id: dict = {}
        try:
            tag_result = await conn.execute(
                sa.select(
                    lifestyle_tags_table.c.name,
                    lifestyle_tags_table.c.categories,
                    lifestyle_tags_table.c.is_inverse,
                )
            )
            tag_mapping = {
                row.name: {"categories": list(row.categories), "is_inverse": row.is_inverse}
                for row in tag_result
            }
        except StopAsyncIteration:
            tag_mapping = {}
    else:
        listing_result = await conn.execute(
            text("""
                SELECT
                    area_id,
                    COALESCE(AVG(CASE WHEN deal_type = 'jeonse' THEN deposit END), 0)::float
                        AS jeonse_ratio_avg,
                    COALESCE(
                        SUM(CASE WHEN flood_risk = true THEN 1 ELSE 0 END)::float
                        / NULLIF(COUNT(*), 0) * 100, 0
                    ) AS flood_ratio,
                    COALESCE(AVG(build_year), 2026)::int AS avg_build_year,
                    COUNT(CASE WHEN deal_type = 'rent'
                        AND deposit <= :deposit_max
                        AND monthly_rent <= :rent_max
                        THEN 1 END)::int AS listing_count,
                    COUNT(CASE WHEN flood_risk = true THEN 1 END)::int AS flood_risk_count
                FROM listings
                WHERE area_id = ANY(:area_ids)
                GROUP BY area_id
            """).bindparams(
                area_ids=area_ids,
                deposit_max=req.deposit_max_wan,
                rent_max=req.monthly_rent_max_wan,
            )
        )
        listing_rows = listing_result.mappings().all()
        listing_by_id = {row.area_id: row for row in listing_rows}

        try:
            tag_result = await conn.execute(
                sa.select(
                    lifestyle_tags_table.c.name,
                    lifestyle_tags_table.c.categories,
                    lifestyle_tags_table.c.is_inverse,
                )
            )
            tag_mapping = {
                row.name: {"categories": list(row.categories), "is_inverse": row.is_inverse}
                for row in tag_result
            }
        except StopAsyncIteration:
            tag_mapping = {}

    priority = "safety" if not req.lifestyle_tags else "life"

    scored = []
    for row, transit in candidates:
        m = metrics_by_id.get(row.area_id)

        if _t077:
            metrics_dict: dict[str, int] = {
                "cafe": getattr(m, "cafe_count", 0) if m else 0,
                "food": getattr(m, "food_count", 0) if m else 0,
                "culture": getattr(m, "culture_count", 0) if m else 0,
                "park": getattr(m, "park_count", 0) if m else 0,
                "subway": getattr(m, "subway_count", 0) if m else 0,
                "hospital": getattr(m, "hospital_count", 0) if m else 0,
                "pharmacy": getattr(m, "pharmacy_count", 0) if m else 0,
                "mart": getattr(m, "mart_count", 0) if m else 0,
            }
            jeonse_raw = getattr(m, "avg_jeonse_ratio", None) if m else None
            flood_raw = getattr(m, "flood_ratio", None) if m else None
            build_year_raw = getattr(m, "avg_build_year", None) if m else None
            listing_count = (getattr(m, "listing_count", 0) if m else 0) or 0
            flood_risk_count = (getattr(m, "flood_risk_count", 0) if m else 0) or 0

            safe = scoring.score_safe(
                60 if jeonse_raw is None else float(jeonse_raw),
                float(flood_raw) if flood_raw is not None else 0,
                int(build_year_raw) if build_year_raw is not None else 2010,
            )
        else:
            metrics_dict = (
                {
                    "cafe": m.cafe,
                    "food": m.food,
                    "culture": m.culture,
                    "park": m.park,
                    "subway": m.subway,
                    "hospital": m.hospital,
                    "pharmacy": m.pharmacy,
                    "mart": m.mart,
                }
                if m is not None
                else {
                    k: 0
                    for k in [
                        "cafe",
                        "food",
                        "culture",
                        "park",
                        "subway",
                        "hospital",
                        "pharmacy",
                        "mart",
                    ]
                }
            )
            lst = listing_by_id.get(row.area_id)
            listing_data = (
                {
                    "jeonse_ratio_avg": lst.jeonse_ratio_avg,
                    "flood_ratio": lst.flood_ratio,
                    "avg_build_year": lst.avg_build_year,
                    "listing_count": lst.listing_count,
                    "flood_risk_count": lst.flood_risk_count,
                }
                if lst is not None
                else dict(_DEFAULT_LISTING)
            )
            listing_count = listing_data["listing_count"]
            flood_risk_count = listing_data["flood_risk_count"]

            safe = scoring.score_safe(
                listing_data["jeonse_ratio_avg"],
                listing_data["flood_ratio"],
                listing_data["avg_build_year"],
            )

        work = scoring.score_work(
            transit["min"],
            req.max_commute_minutes,
            transit.get("transfers", 0),
            transit.get("total_walk_m", 0),
        )
        life = scoring.score_life(metrics_dict, req.lifestyle_tags, tag_mapping)
        scores = {"work": work, "life": round(life), "safe": safe}
        total = scoring.compute_total(scores, priority)

        scored.append((total, row, transit, scores, listing_count, flood_risk_count, m))

    scored.sort(key=lambda x: x[0], reverse=True)

    result: list[dict] = []
    overflow: list[dict] = []  # 예산 매물 없는 동네 (fallback)
    for total, row, transit, scores, lc, frc, m in scored[:20]:
        if len(result) >= 5:
            break
        listing_count, flood_risk_count = lc, frc
        commute_min = transit["min"]
        first_lane = transit.get("first_lane")
        meta = (
            f"{row.sgg_name} · 통근 {commute_min}분"
            if first_lane is None
            else f"{row.sgg_name} · {first_lane} · 통근 {commute_min}분"
        )

        item: dict[str, Any] = {
            "name": row.emd_name,
            "meta": meta,
            "score": total,
            "lat": float(row.lat),
            "lng": float(row.lng),
            "commuteMinutes": commute_min,
            "scores": scores,
            "listing_count": listing_count,
            "flood_risk_count": flood_risk_count,
            "reason": "",
        }

        if _t077:
            try:
                lst_result = await conn.execute(
                    text("""
                        SELECT id, kind, estimated_kind, building_name,
                               deposit, monthly_rent, area_m2, floor,
                               lat, lng, flood_risk, build_year, jibun
                        FROM listings
                        WHERE area_id = :area_id
                          AND deal_type = 'rent'
                          AND deposit <= :deposit_max
                          AND monthly_rent <= :rent_max
                          AND lat IS NOT NULL
                        ORDER BY (deposit + monthly_rent * 12) ASC
                        LIMIT 5
                    """).bindparams(
                        area_id=row.area_id,
                        deposit_max=req.deposit_max_wan,
                        rent_max=req.monthly_rent_max_wan,
                    )
                )
                listings = [
                    {
                        "id": r.id,
                        "kind": r.kind,
                        "estimated_kind": r.estimated_kind,
                        "building_name": r.building_name,
                        "deposit": r.deposit,
                        "monthly_rent": r.monthly_rent,
                        "area_m2": r.area_m2,
                        "floor": r.floor,
                        "lat": r.lat,
                        "lng": r.lng,
                        "flood_risk": r.flood_risk,
                        "build_year": r.build_year,
                        "jibun": r.jibun,
                    }
                    for r in lst_result.fetchall()
                ]
            except StopAsyncIteration:
                listings = []

            jeonse_raw = getattr(m, "avg_jeonse_ratio", None) if m else None
            item.update(
                {
                    "area_id": row.area_id,
                    "listings": listings,
                    "metrics": {
                        "cafe_count": getattr(m, "cafe_count", 0) if m else 0,
                        "food_count": getattr(m, "food_count", 0) if m else 0,
                        "culture_count": getattr(m, "culture_count", 0) if m else 0,
                        "park_count": getattr(m, "park_count", 0) if m else 0,
                        "mart_count": getattr(m, "mart_count", 0) if m else 0,
                        "subway_count": getattr(m, "subway_count", 0) if m else 0,
                        "hospital_count": getattr(m, "hospital_count", 0) if m else 0,
                        "pharmacy_count": getattr(m, "pharmacy_count", 0) if m else 0,
                    },
                    "safety": {
                        "avg_jeonse_ratio": 60 if jeonse_raw is None else float(jeonse_raw),
                        "flood_ratio": float(getattr(m, "flood_ratio", 0) or 0) if m else 0,
                        "avg_build_year": int(getattr(m, "avg_build_year", 2010) or 2010)
                        if m
                        else 2010,
                    },
                }
            )

        # 예산 맞는 매물 있는 동네 우선, 없으면 overflow로 보관(fallback)
        if item.get("listings"):
            result.append(item)
        elif len(overflow) < 5:
            overflow.append(item)

    while len(result) < 5 and overflow:
        result.append(overflow.pop(0))

    for _rank, _item in enumerate(result, 1):
        _item["rank"] = _rank
        _item["tier"] = 1 if _rank == 1 else (2 if _rank <= 3 else 3)

    if session_id is not None:
        match_id: uuid.UUID | None = None
        try:
            r = await conn.execute(
                text("SELECT user_id FROM sessions WHERE id = :session_id"),
                {"session_id": session_id},
            )
            user_id = r.scalar()
            payload_json = json.dumps(req.model_dump(), ensure_ascii=False, default=str)
            r = await conn.execute(
                text(
                    "INSERT INTO profiles (session_id, user_id, payload)"
                    " VALUES (:session_id, :user_id, CAST(:payload AS JSONB)) RETURNING id"
                ),
                {"session_id": session_id, "user_id": user_id, "payload": payload_json},
            )
            profile_id = r.scalar_one()
            r = await conn.execute(
                text(
                    "INSERT INTO match_results (profile_id, payload)"
                    " VALUES (:profile_id, CAST(:payload AS JSONB)) RETURNING id"
                ),
                {
                    "profile_id": profile_id,
                    "payload": json.dumps(
                        {"areas": result, "request": req.model_dump()},
                        ensure_ascii=False,
                        default=str,
                    ),
                },
            )
            match_id = r.scalar_one()
        except SQLAlchemyError as exc:
            logger.warning("recommend_persist_failed", error=str(exc))
        return {"areas": result, "match_id": match_id}

    return result
