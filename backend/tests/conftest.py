import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.database import create_engine, create_schema
from tests.support import make_test_client, sqlite_test_url


@pytest.fixture
def test_engine(tmp_path: Path) -> Iterator[AsyncEngine]:
    engine = create_engine(sqlite_test_url(tmp_path))
    asyncio.run(create_schema(engine))
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture
def api_client(test_engine: AsyncEngine) -> Iterator[TestClient]:
    client = make_test_client(test_engine)
    with client:
        yield client
    client.app.dependency_overrides.clear()
