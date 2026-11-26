"""create price alerts and in-app notification deliveries

Revision ID: 0003_alerts
Revises: 0002_portfolios
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_alerts"
down_revision: str | None = "0002_portfolios"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "price_alerts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("operator", sa.String(length=10), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_price_alerts_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_price_alerts"),
    )
    op.create_index("ix_price_alerts_user_id", "price_alerts", ["user_id"], unique=False)
    op.create_table(
        "alert_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("alert_id", sa.Uuid(), nullable=False),
        sa.Column("triggered_price", sa.Float(), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["alert_id"],
            ["price_alerts.id"],
            name="fk_alert_deliveries_alert_id_price_alerts",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_alert_deliveries"),
        sa.UniqueConstraint("alert_id", "triggered_price", name="uq_alert_deliveries_alert_triggered_price"),
    )
    op.create_index("ix_alert_deliveries_alert_id", "alert_deliveries", ["alert_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_alert_deliveries_alert_id", table_name="alert_deliveries")
    op.drop_table("alert_deliveries")
    op.drop_index("ix_price_alerts_user_id", table_name="price_alerts")
    op.drop_table("price_alerts")
