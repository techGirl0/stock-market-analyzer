from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.connectors.market import DemoMarketDataConnector
from app.core.db import Database
from app.dependencies import get_database, get_instrument_service
from app.main import app
from app.services.instruments import InstrumentService


@pytest.fixture
def api_client(tmp_path: Path) -> Iterator[TestClient]:
    database = Database(str(tmp_path / "test.db"))
    connector = DemoMarketDataConnector()
    app.dependency_overrides[get_database] = lambda: database
    app.dependency_overrides[get_instrument_service] = lambda: InstrumentService(connector)
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
