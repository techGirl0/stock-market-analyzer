import asyncio
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.connectors.market import DemoMarketDataConnector
from app.core.database import create_engine, create_schema, get_session
from app.dependencies import get_instrument_service
from app.main import app
from app.services.instruments import InstrumentService


@pytest.fixture
def api_client(tmp_path: Path) -> Iterator[TestClient]:
    async_engine = create_engine(f"sqlite+aiosqlite:///{tmp_path / 'async-test.db'}")
    asyncio.run(create_schema(async_engine))
    connector = DemoMarketDataConnector()
    app.dependency_overrides[get_instrument_service] = lambda: InstrumentService(connector)

    async def override_session() -> AsyncIterator[object]:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        factory = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.state.test_engine = async_engine
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    asyncio.run(async_engine.dispose())
