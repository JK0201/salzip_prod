import sqlalchemy as sa

from app.db.tables.area_metrics import area_metrics_table
from app.db.tables.area_trends import area_trends_table
from app.db.tables.areas import areas_table
from app.db.tables.hug_accidents import hug_accidents_table
from app.db.tables.listings import listings_table
from app.db.tables.regions import regions_table
from app.services.reb_trend import compute_market_trend
from app.services.risk import compute_risk

_HUG_TYPES = ("주택임차보증", "전세보증금반환보증")
_TREND_METRICS = ("unsold", "apt_tx_monthly", "apt_conv_ratio")


async def get_risk_input(listing_id, conn) -> dict | None:
    stmt = sa.select(
        listings_table.c.flood_risk,
        listings_table.c.flood_year,
        listings_table.c.build_year,
        listings_table.c.area_id,
        listings_table.c.kind,
        listings_table.c.deposit,
        listings_table.c.monthly_rent,
        listings_table.c.area_m2,
    ).where(listings_table.c.id == listing_id)
    listing = (await conn.execute(stmt)).mappings().first()
    if listing is None:
        return None

    # 매물 추정 전세가율 — 환산보증금 / (동네·kind 평당 매매가 × 매물 area_m2)
    # 표본 부족(<5) 또는 매물 정보 결손 시 동네 평균으로 폴백.
    jeonse_ratio: float | None = None
    ratio_source = "listing"
    conv_deposit: int | None = None
    est_sale: float | None = None
    won_per_m2: float | None = None
    sample_n = 0

    if (
        listing["deposit"] is not None
        and listing["area_m2"] is not None
        and float(listing["area_m2"]) > 0
        and listing["kind"]
    ):
        conv_deposit = int(listing["deposit"]) + int(listing["monthly_rent"] or 0) * 100
        sale_stmt = sa.select(
            sa.func.avg(
                listings_table.c.deal_amount
                / sa.func.nullif(listings_table.c.area_m2, 0)
            ).label("won_per_m2"),
            sa.func.count().label("n"),
        ).where(
            listings_table.c.area_id == listing["area_id"],
            listings_table.c.kind == listing["kind"],
            listings_table.c.deal_type == "trade",
            listings_table.c.deal_amount.isnot(None),
            listings_table.c.area_m2 > 0,
        )
        sale_row = (await conn.execute(sale_stmt)).mappings().first()
        if sale_row and sale_row["won_per_m2"] is not None:
            won_per_m2 = float(sale_row["won_per_m2"])
            sample_n = int(sale_row["n"] or 0)
            if sample_n >= 5:
                est_sale = won_per_m2 * float(listing["area_m2"])
                if est_sale > 0:
                    jeonse_ratio = round(conv_deposit / est_sale * 100, 2)

    if jeonse_ratio is None:
        # 폴백 — 동네 평균
        ratio_source = "area_avg"
        stmt = sa.select(area_metrics_table.c.avg_jeonse_ratio).where(
            area_metrics_table.c.area_id == listing["area_id"]
        )
        area_row = (await conn.execute(stmt)).mappings().first()
        _ratio = area_row["avg_jeonse_ratio"] if area_row else None
        jeonse_ratio = float(_ratio) if _ratio is not None else None

    max_year_sq = sa.select(sa.func.max(hug_accidents_table.c.year)).scalar_subquery()
    stmt = sa.select(
        sa.func.sum(hug_accidents_table.c.accident_count).label("accident_count")
    ).where(
        hug_accidents_table.c.guarantee_type.in_(_HUG_TYPES),
        hug_accidents_table.c.year == max_year_sq,
    )
    hug_row = (await conn.execute(stmt)).mappings().first()
    _cnt = hug_row["accident_count"] if hug_row else None
    hug_count = int(_cnt) if _cnt is not None else 0

    stmt = sa.select(regions_table.c.sgg_name).select_from(
        areas_table.join(regions_table, areas_table.c.region_id == regions_table.c.id)
    ).where(areas_table.c.id == listing["area_id"])
    region_row = (await conn.execute(stmt)).mappings().first()
    sgg_name = region_row["sgg_name"] if region_row else None

    region_label = f"서울>{sgg_name}" if sgg_name else ""
    stmt = sa.select(
        area_trends_table.c.metric,
        area_trends_table.c.period,
        area_trends_table.c.value,
    ).where(
        area_trends_table.c.region_label == region_label,
        sa.text("area_trends.metric IN ('unsold', 'apt_tx_monthly', 'apt_conv_ratio')"),
    ).order_by(area_trends_table.c.period.asc())
    trend_rows = (await conn.execute(stmt)).mappings().all()

    series: dict = {}
    for row in trend_rows:
        m = row["metric"]
        if m not in series:
            series[m] = []
        series[m].append((row["period"], row["value"]))

    trend = compute_market_trend(series)

    result = compute_risk(
        jeonse_ratio=jeonse_ratio,
        flood_risk=listing["flood_risk"],
        flood_year=listing["flood_year"],
        build_year=listing["build_year"],
        hug_accident_count=hug_count,
    )
    result["market_trend"] = trend

    # basis 문자열 매물 단위 컨텍스트로 덮어쓰기 — LLM 자연어 해석용.
    for factor in result["factors"]:
        if factor["name"] == "전세가율":
            if ratio_source == "listing" and conv_deposit and est_sale:
                factor["basis"] = (
                    f"이 매물 추정 전세가율 {jeonse_ratio}% "
                    f"(환산보증금 {conv_deposit:,}만원 / 동네 {listing['kind']} 평당 매매가 "
                    f"{won_per_m2:,.0f}만원·{listing['area_m2']}㎡ 기준 추정 매매가 "
                    f"{est_sale:,.0f}만원, 표본 {sample_n}건)"
                )
            else:
                factor["basis"] = (
                    f"동네 평균 전세가율 {jeonse_ratio}% (매물 매매가 표본 부족으로 동네 평균 폴백)"
                )
        elif factor["name"] == "HUG":
            if ratio_source == "listing":
                factor["basis"] = f"이 매물 추정 전세가율 {jeonse_ratio}% 기준 HUG 가입 가능성"
            else:
                factor["basis"] = f"동네 평균 전세가율 {jeonse_ratio}% 기준 HUG 가입 가능성"

    result["jeonse_ratio_source"] = ratio_source
    return result
