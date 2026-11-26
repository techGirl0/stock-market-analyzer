import asyncio
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.connectors.market import DemoMarketDataConnector
from app.core.database import create_engine, create_schema, get_session
from app.dependencies import get_instrument_service
from app.main import app
from app.services.instruments import InstrumentService


def before_all(context):
    context.api_base_url = os.getenv("API_BASE_URL")
    if context.api_base_url:
        import httpx

        context.client = httpx.Client(base_url=context.api_base_url)
        return
    context.temp_dir = tempfile.TemporaryDirectory()
    path = Path(context.temp_dir.name)
    context.async_engine = create_engine(f"sqlite+aiosqlite:///{path / 'async.db'}")
    asyncio.run(create_schema(context.async_engine))
    app.dependency_overrides[get_instrument_service] = lambda: InstrumentService(DemoMarketDataConnector())

    async def override_session():
        from sqlalchemy.ext.asyncio import async_sessionmaker

        async with async_sessionmaker(context.async_engine, expire_on_commit=False)() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    context.client = TestClient(app)


def after_all(context):
    context.client.close()
    app.dependency_overrides.clear()
    if hasattr(context, "async_engine"):
        asyncio.run(context.async_engine.dispose())
    if hasattr(context, "temp_dir"):
        context.temp_dir.cleanup()
