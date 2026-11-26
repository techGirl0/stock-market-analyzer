"""
SCRUM-68: price alerts, in-app notifications and the evaluation worker on
SQLAlchemy. Fake provider, fake clock; no network calls.
"""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.core.database import create_engine, create_schema
from app.models import AlertDelivery, PriceAlert, User
from app.services.alerts import AlertService


def register(client, email="alerts@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def headers(token):
    return {"Authorization": f"Bearer {token}"}


class FixedPriceInstruments:
    """Fake instrument service: a fixed price for every symbol.

    price=None simulates the provider failing with an exception, which the
    evaluation must survive without creating notifications.
    """

    def __init__(self, price: float | None) -> None:
        self.price = price
        self.quote_calls = 0

    async def quote(self, symbol: str):
        self.quote_calls += 1
        if self.price is None:
            raise RuntimeError("provider down")
        from app.schemas.v1 import Availability, DataMeta, Instrument, Quote

        now = datetime.now(timezone.utc)
        return Quote(
            instrument=Instrument(id=uuid4(), symbol=symbol, name=symbol),
            price=self.price,
            as_of=now,
            meta=DataMeta(source="demo", fetched_at=now, availability=Availability.available, delayed=False),
        )


class UnavailablePriceInstruments(FixedPriceInstruments):
    """Price present in the response but marked unavailable (price=None on the quote)."""

    async def quote(self, symbol: str):
        self.quote_calls += 1
        from app.schemas.v1 import Availability, DataMeta, Instrument, Quote

        now = datetime.now(timezone.utc)
        return Quote(
            instrument=Instrument(id=uuid4(), symbol=symbol, name=symbol),
            price=None,
            as_of=now,
            meta=DataMeta(source="demo", fetched_at=now, availability=Availability.unavailable, delayed=False),
        )


def _evaluate(api_client, instruments, **kwargs) -> int:
    """Run one evaluation cycle against the test engine with a fake provider."""

    async def _run() -> int:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        engine = api_client.app.state.test_engine
        factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with factory() as session:
            service = AlertService(session, instruments)
            return await service.evaluate_active(**kwargs)

    return asyncio.run(_run())


def test_alert_crud_and_isolation(api_client):
    token = register(api_client)
    auth = headers(token)

    created = api_client.post(
        "/api/v1/alerts",
        headers=auth,
        json={"symbol": "aapl", "operator": "above", "threshold": 100},
    )
    assert created.status_code == 201
    alert = created.json()
    assert alert["symbol"] == "AAPL"
    assert alert["active"] is True
    alert_id = alert["id"]

    listed = api_client.get("/api/v1/alerts", headers=auth)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == alert_id

    unknown = api_client.post(
        "/api/v1/alerts",
        headers=auth,
        json={"symbol": "XXXX", "operator": "above", "threshold": 1},
    )
    assert unknown.status_code == 404

    other = register(api_client, "other@example.com")
    assert api_client.get("/api/v1/alerts", headers=headers(other)).json() == []
    assert api_client.delete(f"/api/v1/alerts/{alert_id}", headers=headers(other)).status_code == 404
    assert api_client.delete(f"/api/v1/alerts/{alert_id}", headers=auth).status_code == 204
    assert api_client.get("/api/v1/alerts", headers=auth).json() == []


def test_evaluation_creates_exactly_one_notification(api_client):
    token = register(api_client)
    auth = headers(token)
    api_client.post(
        "/api/v1/alerts",
        headers=auth,
        json={"symbol": "AAPL", "operator": "above", "threshold": 100},
    )

    fake = FixedPriceInstruments(price=150.0)
    fixed_clock = lambda: datetime(2026, 11, 26, 12, 0, tzinfo=timezone.utc)  # noqa: E731

    first = _evaluate(api_client, fake, clock=fixed_clock, max_attempts=1, backoff_base_seconds=0)
    second = _evaluate(api_client, fake, clock=fixed_clock, max_attempts=1, backoff_base_seconds=0)
    assert first == 1
    assert second == 0, "re-evaluation at the same price must not notify again"

    notifications = api_client.get("/api/v1/alerts/notifications", headers=auth)
    assert notifications.status_code == 200
    body = notifications.json()
    assert len(body) == 1
    delivery = body[0]
    assert delivery["triggered_price"] == 150.0
    assert delivery["read"] is False
    # the fake clock controls the delivery time (sqlite returns it naive)
    assert delivery["delivered_at"].startswith("2026-11-26T12:00:00")
    message = delivery["message"]
    assert "AAPL" in message and "above" in message and "$100.00" in message
    assert "buy" not in message.lower() and "sell" not in message.lower()

    marked = api_client.post(f"/api/v1/alerts/notifications/{delivery['id']}/read", headers=auth)
    assert marked.status_code == 200
    assert marked.json()["read"] is True
    assert api_client.get("/api/v1/alerts/notifications", headers=auth).json()[0]["read"] is True


def test_unmet_condition_never_notifies(api_client):
    token = register(api_client)
    auth = headers(token)
    api_client.post(
        "/api/v1/alerts",
        headers=auth,
        json={"symbol": "AAPL", "operator": "above", "threshold": 100},
    )

    assert _evaluate(api_client, FixedPriceInstruments(price=50.0), max_attempts=1, backoff_base_seconds=0) == 0
    assert api_client.get("/api/v1/alerts/notifications", headers=auth).json() == []


def test_provider_failure_and_unavailable_price_never_notify(api_client):
    token = register(api_client)
    auth = headers(token)
    api_client.post(
        "/api/v1/alerts",
        headers=auth,
        json={"symbol": "AAPL", "operator": "above", "threshold": 100},
    )

    # provider raises every time: bounded retries, then skipped
    failing = FixedPriceInstruments(price=None)
    assert _evaluate(api_client, failing, max_attempts=2, backoff_base_seconds=0) == 0
    assert failing.quote_calls == 2, "must retry with bounded attempts"

    # quote present but price unavailable: skipped immediately
    unavailable = UnavailablePriceInstruments(price=None)
    assert _evaluate(api_client, unavailable, max_attempts=2, backoff_base_seconds=0) == 0
    assert unavailable.quote_calls == 1

    assert api_client.get("/api/v1/alerts/notifications", headers=auth).json() == []


def test_notification_isolation(api_client):
    token = register(api_client)
    other = register(api_client, "other@example.com")
    auth = headers(token)
    assert api_client.get("/api/v1/alerts/notifications", headers=headers(other)).json() == []
    assert api_client.post(
        f"/api/v1/alerts/notifications/{uuid4()}/read", headers=auth
    ).status_code == 404


def test_alert_orm_cascade_direct():
    """Direct ORM check: deleting a user cascades to alerts and deliveries."""

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
            alert = PriceAlert(
                id=uuid4(),
                user_id=user.id,
                symbol="AAPL",
                operator="above",
                threshold=100.0,
                active=True,
                created_at=datetime.now(timezone.utc),
            )
            delivery = AlertDelivery(
                id=uuid4(),
                alert_id=alert.id,
                triggered_price=150.0,
                message="test",
                read=False,
                delivered_at=datetime.now(timezone.utc),
            )
            session.add_all([user, alert, delivery])
            await session.commit()
            user_id, alert_id = user.id, alert.id

        async with factory() as session:
            user = await session.get(User, user_id)
            await session.delete(user)
            await session.commit()

        async with factory() as session:
            assert (await session.get(PriceAlert, alert_id)) is None
            assert (await session.scalar(select(AlertDelivery).limit(1))) is None
        await engine.dispose()

    asyncio.run(_run())
