import os
import subprocess
import sys
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import (
    AlertDelivery,
    Portfolio,
    PortfolioHolding,
    PriceAlert,
    User,
    Watchlist,
    WatchlistItem,
)

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)


async def _migrated_postgres_session():
    """Run alembic migrations against TEST_DATABASE_URL and yield a session factory."""
    database_url = os.environ["TEST_DATABASE_URL"]
    environment = {**os.environ, "DATABASE_URL": database_url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
        check=False,
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, factory


@pytest.mark.asyncio
async def test_postgres_schema_and_user_cascade() -> None:
    engine, factory = await _migrated_postgres_session()
    user_id = uuid4()
    async with factory() as session:
        user = User(
            id=user_id,
            email=f"postgres-{user_id.hex}@example.test",
            password_hash="test-hash",
            created_at=datetime.now(timezone.utc),
        )
        watchlist = Watchlist(name="Postgres test", created_at=user.created_at, user=user)
        watchlist.items.append(
            WatchlistItem(symbol="AAPL", created_at=user.created_at)
        )
        session.add(user)
        await session.commit()

        assert await session.scalar(select(func.count()).select_from(WatchlistItem)) == 1
        await session.delete(user)
        await session.commit()
        assert await session.scalar(select(func.count()).select_from(Watchlist)) == 0
        assert await session.scalar(select(func.count()).select_from(WatchlistItem)) == 0
    await engine.dispose()


@pytest.mark.asyncio
async def test_postgres_portfolio_and_alert_cascade() -> None:
    """Migrations 0002/0003 create the financial-domain tables on PostgreSQL
    and account deletion cascades through portfolios, holdings, alerts and
    deliveries."""
    engine, factory = await _migrated_postgres_session()
    user_id = uuid4()
    async with factory() as session:
        user = User(
            id=user_id,
            email=f"postgres-{user_id.hex}@example.test",
            password_hash="test-hash",
            created_at=datetime.now(timezone.utc),
        )
        portfolio = Portfolio(name="Integration", created_at=user.created_at, user=user)
        portfolio.holdings.append(
            PortfolioHolding(symbol="AAPL", quantity=3.0, created_at=user.created_at)
        )
        alert = PriceAlert(
            symbol="AAPL",
            operator="above",
            threshold=100.0,
            active=True,
            created_at=user.created_at,
            user=user,
        )
        alert.deliveries.append(
            AlertDelivery(
                triggered_price=150.0,
                message="AAPL is trading at $150.00, above your $100.00 threshold.",
                read=False,
                delivered_at=user.created_at,
            )
        )
        session.add(user)
        await session.commit()

        assert await session.scalar(select(func.count()).select_from(PortfolioHolding)) == 1
        assert await session.scalar(select(func.count()).select_from(AlertDelivery)) == 1
        await session.delete(user)
        await session.commit()
        for model in (Portfolio, PortfolioHolding, PriceAlert, AlertDelivery):
            assert await session.scalar(select(func.count()).select_from(model)) == 0
    await engine.dispose()
