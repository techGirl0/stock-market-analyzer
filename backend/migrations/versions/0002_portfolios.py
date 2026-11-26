"""create portfolios and holdings schema

Revision ID: 0002_portfolios
Revises: 0001_initial_schema
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_portfolios"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_portfolios_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_portfolios"),
    )
    op.create_index("ix_portfolios_user_id", "portfolios", ["user_id"], unique=False)
    op.create_table(
        "portfolio_holdings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["portfolio_id"],
            ["portfolios.id"],
            name="fk_portfolio_holdings_portfolio_id_portfolios",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_holdings"),
        sa.UniqueConstraint("portfolio_id", "symbol", name="uq_portfolio_holdings_portfolio_symbol"),
    )
    op.create_index("ix_portfolio_holdings_portfolio_id", "portfolio_holdings", ["portfolio_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_portfolio_holdings_portfolio_id", table_name="portfolio_holdings")
    op.drop_table("portfolio_holdings")
    op.drop_index("ix_portfolios_user_id", table_name="portfolios")
    op.drop_table("portfolios")
