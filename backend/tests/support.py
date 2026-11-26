"""Shared test support: app client factory and auth helpers.

Used by both the pytest suite (via conftest.py) and the behave BDD suite
(via features/environment.py) so the two wire up the app exactly once.
"""

from collections.abc import AsyncIterator

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.connectors.market import DemoMarketDataConnector
from app.core.database import get_session
from app.dependencies import get_instrument_service
from app.main import app
from app.services.instruments import InstrumentService


def make_test_client(engine: AsyncEngine) -> TestClient:
    """TestClient wired to the given engine and the demo market provider."""
    app.dependency_overrides[get_instrument_service] = lambda: InstrumentService(DemoMarketDataConnector())

    async def override_session() -> AsyncIterator[AsyncSession]:
        factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    return TestClient(app)


def register(client: TestClient, email: str = "user@example.com", password: str = "Password123!") -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def sqlite_test_url(directory, name: str = "test.db") -> str:
    return f"sqlite+aiosqlite:///{directory / name}"
