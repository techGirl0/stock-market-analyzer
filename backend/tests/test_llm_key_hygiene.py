"""SCRUM-69: the LLM API key must never leak into logs or error responses."""

import logging

import pytest

from app.connectors.llm import GroqLLMConnector
from app.core.errors import BackendError

FAKE_KEY = "gsk-TEST-SECRET-KEY-DO-NOT-LEAK"


class _Completions:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def create(self, **kwargs):
        raise self._exc


class _Chat:
    def __init__(self, exc: Exception) -> None:
        self.completions = _Completions(exc)


class _FakeClient:
    def __init__(self, exc: Exception) -> None:
        self.chat = _Chat(exc)


@pytest.fixture()
def groq_connector() -> GroqLLMConnector:
    return GroqLLMConnector(
        api_key=FAKE_KEY,
        model="qwen/test",
        client=_FakeClient(RuntimeError("connection refused to api.groq.com")),
    )


@pytest.fixture(autouse=True)
def _no_retry_sleep(monkeypatch):
    """Retry backoff would sleep several seconds; tests don't need it."""
    monkeypatch.setattr("app.connectors.llm.time.sleep", lambda _s: None)


@pytest.mark.asyncio
async def test_llm_key_never_logged_or_returned(groq_connector, caplog):
    with caplog.at_level(logging.DEBUG, logger="app.connectors.llm"):
        with pytest.raises(BackendError) as exc_info:
            await groq_connector.brief("AAPL", "price 100")

    leaked_records = [r for r in caplog.records if FAKE_KEY in (r.getMessage() or "")]
    assert not leaked_records, "API key must not appear in any log record"
    assert FAKE_KEY not in caplog.text
    assert FAKE_KEY not in str(exc_info.value)
    assert FAKE_KEY not in repr(exc_info.value)
    if exc_info.value.details:
        assert FAKE_KEY not in str(exc_info.value.details)


@pytest.mark.asyncio
async def test_llm_key_never_logged_on_rate_limit(caplog):
    connector = GroqLLMConnector(
        api_key=FAKE_KEY,
        model="qwen/test",
        client=_FakeClient(RuntimeError("RateLimitError 429 quota exceeded")),
    )

    with caplog.at_level(logging.DEBUG, logger="app.connectors.llm"):
        with pytest.raises(BackendError) as exc_info:
            await connector.chat("AAPL", "price 100", [])

    assert FAKE_KEY not in caplog.text
    assert FAKE_KEY not in str(exc_info.value)
    assert exc_info.value.status_code == 429
