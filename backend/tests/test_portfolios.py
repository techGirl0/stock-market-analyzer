"""
SCRUM-67: portfolio CRUD and holdings valuation on SQLAlchemy.
Covers CRUD, valuation with a fake provider, unavailable price,
per-user isolation and cascade on account deletion.
"""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.core.database import create_engine, create_schema
from app.dependencies import get_instrument_service
from app.main import app
from app.models import Portfolio, PortfolioHolding, User
from app.schemas.v1 import Availability, DataMeta, Instrument, Quote


def register(client, email="portfolio@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def headers(token):
    return {"Authorization": f"Bearer {token}"}


class UnavailablePriceInstruments:
    """Fake instrument service: symbols validate, but prices are unavailable."""

    async def quote(self, symbol: str) -> Quote:
        now = datetime.now(timezone.utc)
        return Quote(
            instrument=Instrument(id=uuid4(), symbol=symbol, name=symbol),
            price=None,
            as_of=now,
            meta=DataMeta(source="demo", fetched_at=now, availability=Availability.unavailable, delayed=False),
        )


def test_portfolio_crud_and_valuation(api_client):
    token = register(api_client)
    auth = headers(token)

    created = api_client.post("/api/v1/portfolios", headers=auth, json={"name": "Growth"})
    assert created.status_code == 201
    portfolio_id = created.json()["id"]
    assert created.json()["total_value"] is None

    added = api_client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        headers=auth,
        json={"symbol": "aapl", "quantity": 10},
    )
    assert added.status_code == 201
    holding = added.json()
    assert holding["current_price"] is not None
    assert holding["current_value"] == pytest.approx(holding["current_price"] * 10)
    assert holding["price_source"] == "demo"
    assert holding["price_as_of"] is not None
    holding_id = holding["id"]

    duplicate = api_client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        headers=auth,
        json={"symbol": "AAPL", "quantity": 5},
    )
    assert duplicate.status_code == 409

    fetched = api_client.get(f"/api/v1/portfolios/{portfolio_id}", headers=auth)
    assert fetched.status_code == 200
    body = fetched.json()
    assert len(body["holdings"]) == 1
    assert body["total_value"] == pytest.approx(body["holdings"][0]["current_value"])
    assert body["value_as_of"] is not None

    listed = api_client.get("/api/v1/portfolios", headers=auth)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == portfolio_id

    assert api_client.delete(
        f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}", headers=auth
    ).status_code == 204
    assert api_client.delete(f"/api/v1/portfolios/{portfolio_id}", headers=auth).status_code == 204
    assert api_client.get(f"/api/v1/portfolios/{portfolio_id}", headers=auth).status_code == 404


def test_portfolio_unavailable_price_is_reported_not_defaulted(api_client):
    token = register(api_client, "unavailable@example.com")
    auth = headers(token)
    app.dependency_overrides[get_instrument_service] = lambda: UnavailablePriceInstruments()
    try:
        portfolio_id = api_client.post("/api/v1/portfolios", headers=auth, json={"name": "Flat"}).json()["id"]
        added = api_client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            headers=auth,
            json={"symbol": "AAPL", "quantity": 3},
        )
        assert added.status_code == 201
        holding = added.json()
        assert holding["current_price"] is None
        assert holding["current_value"] is None

        fetched = api_client.get(f"/api/v1/portfolios/{portfolio_id}", headers=auth).json()
        assert fetched["total_value"] is None
        assert fetched["value_as_of"] is None
    finally:
        app.dependency_overrides.pop(get_instrument_service, None)


def test_portfolio_isolation_and_authentication(api_client):
    first = register(api_client, "owner@example.com")
    second = register(api_client, "intruder@example.com")
    portfolio_id = api_client.post(
        "/api/v1/portfolios", headers=headers(first), json={"name": "Private"}
    ).json()["id"]

    assert api_client.get(f"/api/v1/portfolios/{portfolio_id}", headers=headers(second)).status_code == 404
    assert api_client.delete(f"/api/v1/portfolios/{portfolio_id}", headers=headers(second)).status_code == 404
    assert api_client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        headers=headers(second),
        json={"symbol": "AAPL", "quantity": 1},
    ).status_code == 404
    assert api_client.get("/api/v1/portfolios").status_code == 401

    unknown = api_client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        headers=headers(first),
        json={"symbol": "XXXX", "quantity": 1},
    )
    assert unknown.status_code == 404
    assert unknown.json()["error"]["message"] == 'Ticker "XXXX" was not found.'


def test_portfolio_cascade_on_account_deletion(api_client):
    token = register(api_client, "deleteme@example.com")
    auth = headers(token)
    portfolio_id = api_client.post("/api/v1/portfolios", headers=auth, json={"name": "Doomed"}).json()["id"]
    api_client.post(
        f"/api/v1/portfolios/{portfolio_id}/holdings",
        headers=auth,
        json={"symbol": "AAPL", "quantity": 2},
    )

    assert api_client.delete("/api/v1/auth/me", headers=auth).status_code == 204

    # a fresh account on the same email starts with zero portfolios; the ORM
    # cascade itself is covered by test_portfolio_orm_cascade_direct below.
    fresh = register(api_client, "deleteme@example.com")
    listed = api_client.get("/api/v1/portfolios", headers=headers(fresh))
    assert listed.status_code == 200
    assert listed.json() == []


def test_portfolio_orm_cascade_direct():
    """Direct ORM check: deleting a user cascades to portfolios and holdings."""
    async def _run() -> None:
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        engine = create_engine("sqlite+aiosqlite://")
        await create_schema(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

        async with factory() as session:
            user = User(
                id=uuid4(),
                email=f"{uuid4()}@example.com",
                password_hash="x",
                created_at=datetime.now(timezone.utc),
            )
            portfolio = Portfolio(
                id=uuid4(),
                user_id=user.id,
                name="Cascade",
                created_at=datetime.now(timezone.utc),
            )
            holding = PortfolioHolding(
                id=uuid4(),
                portfolio_id=portfolio.id,
                symbol="AAPL",
                quantity=1.0,
                created_at=datetime.now(timezone.utc),
            )
            session.add_all([user, portfolio, holding])
            await session.commit()
            user_id = user.id
            portfolio_id = portfolio.id

        async with factory() as session:
            user = await session.get(User, user_id)
            await session.delete(user)
            await session.commit()

        async with factory() as session:
            assert (await session.get(Portfolio, portfolio_id)) is None
            assert (await session.scalar(select(PortfolioHolding).limit(1))) is None
        await engine.dispose()

    asyncio.run(_run())
