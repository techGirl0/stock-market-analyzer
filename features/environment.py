"""Behave environment: wires the real FastAPI app to an isolated test database.

Reuses the same client factory as the pytest suite (backend/tests/support.py)
so the two suites set up the app exactly once, the same way.
"""

import asyncio
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# The BDD suite makes many requests per run; the global per-IP limiter is a
# DoS guard for real traffic, not a constraint the acceptance suite should hit.
os.environ.setdefault("API_RATE_LIMIT", "100000")

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import create_engine, create_schema  # noqa: E402
from app.core.rate_limit import auth_limiter, research_limiter  # noqa: E402
from app.main import api_limiter  # noqa: E402
from tests.support import make_test_client, sqlite_test_url  # noqa: E402


def before_all(context):
    context.tmp_dir = TemporaryDirectory()
    engine = create_engine(sqlite_test_url(Path(context.tmp_dir.name)))
    asyncio.run(create_schema(engine))
    context.client = make_test_client(engine)
    context.engine = engine
    from app.dependencies import get_instrument_service

    context.default_instruments = context.client.app.dependency_overrides[get_instrument_service]


def after_all(context):
    context.client.app.dependency_overrides.clear()
    asyncio.run(context.engine.dispose())
    context.tmp_dir.cleanup()


def after_scenario(context, scenario):
    # Per-user/per-IP limiters persist across scenarios in one process; each
    # scenario deserves a fresh budget. Provider overrides (outage, short
    # history) are restored to the default demo provider.
    auth_limiter.reset()
    research_limiter.reset()
    api_limiter.reset()
    from app.dependencies import get_instrument_service

    context.client.app.dependency_overrides[get_instrument_service] = context.default_instruments
