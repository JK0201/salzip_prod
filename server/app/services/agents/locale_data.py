import sqlalchemy as sa

from app.db.tables.area_metrics import area_metrics_table
from app.db.tables.areas import areas_table
from app.db.tables.listings import listings_table


async def get_locale_input(listing_id, conn) -> dict | None:
    listing_stmt = sa.select(listings_table.c.area_id).where(
        listings_table.c.id == listing_id
    )
    listing = (await conn.execute(listing_stmt)).mappings().first()
    if listing is None:
        return None

    area_id = listing["area_id"]

    metrics_stmt = sa.select(
        area_metrics_table.c.mart_count,
        area_metrics_table.c.cafe_count,
        area_metrics_table.c.food_count,
        area_metrics_table.c.hospital_count,
        area_metrics_table.c.pharmacy_count,
        area_metrics_table.c.culture_count,
        area_metrics_table.c.subway_count,
        area_metrics_table.c.park_count,
    ).where(area_metrics_table.c.area_id == area_id)
    metrics = (await conn.execute(metrics_stmt)).mappings().first()
    if metrics is None:
        return None

    area_stmt = sa.select(areas_table.c.emd_name).where(areas_table.c.id == area_id)
    area = (await conn.execute(area_stmt)).mappings().first()

    mart_count = metrics["mart_count"]
    cafe_count = metrics["cafe_count"]
    food_count = metrics["food_count"]
    hospital_count = metrics["hospital_count"]
    pharmacy_count = metrics["pharmacy_count"]
    culture_count = metrics["culture_count"]
    subway_count = metrics["subway_count"]
    park_count = metrics["park_count"]

    return {
        "counts": {
            "cafe": cafe_count,
            "food": food_count,
            "culture": culture_count,
            "park": park_count,
            "mart": mart_count,
            "subway": subway_count,
            "hospital": hospital_count,
            "pharmacy": pharmacy_count,
        },
        "subway_access": bool(subway_count > 0),
        "medical": hospital_count + pharmacy_count,
        "convenience": cafe_count + food_count + mart_count,
        "green": park_count,
        "area_name": area["emd_name"] if area else None,
    }
