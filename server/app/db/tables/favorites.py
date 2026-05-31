import sqlalchemy as sa

from app.db.tables import metadata

favorites_table = sa.Table(
    "favorites",
    metadata,
    sa.Column(
        "user_id",
        sa.UUID(),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "listing_id",
        sa.UUID(),
        sa.ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
    sa.PrimaryKeyConstraint("user_id", "listing_id"),
    sa.Index("ix_favorites_user_id", "user_id"),
)
