from sqlalchemy import MetaData

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

from app.db.tables import (  # noqa: F401, E402
    area_metrics,
    area_places,
    area_trends,
    areas,
    commute_cache,
    favorites,
    hug_accidents,
    job_categories,
    lifestyle_tags,
    listings,
    match_results,
    profiles,
    regions,
    sessions,
    support_programs,
    users,
)
from app.db.tables.job_categories import (  # noqa: E402
    job_categories_table as job_categories_table,
)
from app.db.tables.lifestyle_tags import (  # noqa: E402
    lifestyle_tags_table as lifestyle_tags_table,
)
