import sqlalchemy as sa

from app.db.tables.listings import listings_table


async def get_sise_input(listing_id, conn) -> dict | None:
    stmt = sa.select(
        listings_table.c.deposit,
        listings_table.c.monthly_rent,
        listings_table.c.area_id,
        listings_table.c.estimated_kind,
        listings_table.c.deal_type,
    ).where(listings_table.c.id == listing_id)
    listing = (await conn.execute(stmt)).mappings().first()
    if listing is None:
        return None

    target_conv = (listing["deposit"] or 0) + (listing["monthly_rent"] or 0) * 100

    dist = await _query_dist(
        conn,
        area_id=listing["area_id"],
        deal_type=listing["deal_type"],
        estimated_kind=listing["estimated_kind"],
        with_kind=True,
    )

    if dist["sample_size"] < 5:
        dist = await _query_dist(
            conn,
            area_id=listing["area_id"],
            deal_type=listing["deal_type"],
            estimated_kind=listing["estimated_kind"],
            with_kind=False,
        )

    if dist["sample_size"] == 0:
        return None

    median_conv = dist["median_conv"]
    sample_size = dist["sample_size"]
    ratio = target_conv / median_conv if median_conv else None

    if target_conv <= median_conv * 0.85:
        verdict = "저렴"
    elif target_conv <= median_conv * 1.15:
        verdict = "적정"
    else:
        verdict = "비쌈"

    return {
        "target_conv": target_conv,
        "median_conv": median_conv,
        "sample_size": sample_size,
        "ratio": ratio,
        "percentile": 0.5,
        "verdict": verdict,
        "deal_type": listing["deal_type"],
        "kind": listing["estimated_kind"],
    }


async def _query_dist(conn, *, area_id, deal_type, estimated_kind, with_kind: bool) -> dict:
    conv_expr = listings_table.c.deposit + listings_table.c.monthly_rent * 100
    conditions = [
        listings_table.c.area_id == area_id,
        listings_table.c.deal_type == deal_type,
    ]
    if with_kind:
        conditions.append(listings_table.c.estimated_kind == estimated_kind)

    stmt = sa.select(
        sa.func.count().label("sample_size"),
        sa.func.percentile_cont(0.5).within_group(conv_expr).label("median_conv"),
    ).where(*conditions)
    row = (await conn.execute(stmt)).mappings().first()
    return {
        "sample_size": row["sample_size"] if row else 0,
        "median_conv": row["median_conv"] if row else None,
    }
