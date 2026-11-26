"""SCRUM-119: contract tests for YFinanceMarketDataConnector.

Every fixture below is a recorded provider response — the JSON Yahoo's search
endpoint returns and the dict/list shapes the yfinance library hands back —
replayed through the real connector. Nothing here touches the network, and
because Yahoo's endpoints are keyless no recorded response can contain a
credential. The demo connector keeps its own coverage via the API-level suite
(test_instruments.py), so this file only pins the yfinance contract.
"""

import asyncio
import sys
from datetime import datetime, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any
from uuid import uuid5

import httpx
import pytest

from app.connectors.market import (
    INSTRUMENT_NS,
    NEWS_NS,
    ConnectorUnavailable,
    YFinanceMarketDataConnector,
)

# --- recorded provider responses -------------------------------------------

RECORDED_SEARCH_RESPONSE: dict[str, Any] = {
    "quotes": [
        {
            "symbol": "AAPL",
            "shortname": "Apple Inc.",
            "longname": "Apple Inc.",
            "exchange": "NMS",
            "currency": "USD",
            "quoteType": "EQUITY",
        },
        {
            "symbol": "APLE",
            "longname": "Apple Hospitality REIT Inc",
            "exchange": "NYQ",
            "currency": "USD",
            "quoteType": "EQUITY",
        },
        # Malformed entries occasionally appear in the feed; the contract
        # says they are skipped, never defaulted.
        {"longname": "Entry with no symbol"},
        {"symbol": "NOT-A-REAL-TICKER-BUT-WAY-TOO-LONG", "longname": "Junk"},
    ]
}

RECORDED_AAPL_INFO: dict[str, Any] = {
    "quoteType": "EQUITY",
    "shortName": "Apple Inc.",
    "longName": "Apple Inc.",
    "exchange": "NMS",
    "currency": "USD",
    "currentPrice": 233.25,
    "previousClose": 231.04,
    "regularMarketVolume": 41_234_567,
    "marketCap": 3_523_000_000_000,
    "trailingPE": 35.412,
    "beta": 1.24,
}

RECORDED_HISTORY_ROWS: list[dict[str, Any]] = [
    {
        "timestamp": datetime(2026, 11, 24, 14, 30, tzinfo=timezone.utc),
        "Open": 230.10,
        "High": 233.40,
        "Low": 229.85,
        "Close": 233.25,
        "Volume": 41_234_567,
    },
    {
        "timestamp": datetime(2026, 11, 25, 14, 30, tzinfo=timezone.utc),
        "Open": 233.30,
        "High": 234.94,
        "Low": 232.11,
        "Close": 234.40,
        "Volume": 35_111_222,
    },
]

RECORDED_NEWS: list[dict[str, Any]] = [
    {
        "content": {
            "title": "Apple unveils new AI strategy",
            "pubDate": "2026-11-20T18:30:00Z",
            "canonicalUrl": {"url": "https://finance.yahoo.com/news/apple-unveils-ai-123456.html"},
            "provider": {"displayName": "Yahoo Finance"},
        }
    },
    # Legacy flat shape still emitted by older yfinance releases.
    {
        "title": "Legacy headline from an older feed",
        "link": "https://finance.yahoo.com/news/legacy-789.html",
        "pubDate": "2026-11-19T09:15:00Z",
        "provider": {"displayName": "Reuters"},
    },
    # Incomplete entries are skipped, never partially defaulted.
    {"content": {"title": "No url or date, must be skipped"}},
    {"content": {}},
]


# --- fakes that replay the recordings ----------------------------------------


class _RecordedResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


class _ReplayingAsyncClient:
    """Stands in for httpx.AsyncClient; replays a recorded Yahoo response."""

    def __init__(self, reply: _RecordedResponse | Exception, **kwargs: Any) -> None:
        self._reply = reply

    async def __aenter__(self) -> "_ReplayingAsyncClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None

    async def get(self, url: str, **kwargs: Any) -> _RecordedResponse:
        if isinstance(self._reply, Exception):
            raise self._reply
        return self._reply


class _RecordedTimestamp:
    """Duck-typed pandas Timestamp: only to_pydatetime is on the contract."""

    def __init__(self, value: datetime) -> None:
        self._value = value

    def to_pydatetime(self) -> datetime:
        return self._value


class _RecordedHistory:
    """Duck-typed yfinance history DataFrame; only iterrows is on the contract."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def iterrows(self) -> Any:
        for row in self._rows:
            yield _RecordedTimestamp(row["timestamp"]), row


class _RecordedTicker:
    """Replays recorded info/history/news for any symbol."""

    def __init__(
        self,
        info: dict[str, Any],
        history: _RecordedHistory | None = None,
        news: list[dict[str, Any]] | None = None,
    ) -> None:
        self._info = info
        self._history = history
        self._news = news

    @property
    def info(self) -> dict[str, Any]:
        return self._info

    @property
    def news(self) -> list[dict[str, Any]]:
        return self._news or []

    def history(self, start: Any, end: Any, interval: Any) -> _RecordedHistory:
        return self._history or _RecordedHistory([])


class _FailingTicker:
    """Simulates a provider outage: every access raises."""

    @property
    def info(self) -> dict[str, Any]:
        raise RuntimeError("recorded provider outage")

    @property
    def news(self) -> list[dict[str, Any]]:
        raise RuntimeError("recorded provider outage")

    def history(self, start: Any, end: Any, interval: Any) -> _RecordedHistory:
        raise RuntimeError("recorded provider outage")


class _FakeYFinance(ModuleType):
    def __init__(self, ticker_cls: Any) -> None:
        super().__init__("yfinance")
        self.Ticker = ticker_cls


def make_connector(monkeypatch: pytest.MonkeyPatch, ticker_cls: Any) -> YFinanceMarketDataConnector:
    """Build the real connector against a recorded yfinance module."""
    monkeypatch.setitem(sys.modules, "yfinance", _FakeYFinance(ticker_cls))
    return YFinanceMarketDataConnector()


def make_search_connector(
    monkeypatch: pytest.MonkeyPatch, reply: _RecordedResponse | Exception
) -> YFinanceMarketDataConnector:
    """Build the real connector with httpx replaying a recorded search reply."""
    connector = make_connector(monkeypatch, _RecordedTicker)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: _ReplayingAsyncClient(reply))
    return connector


# --- search ------------------------------------------------------------------


def test_search_normalizes_recorded_yahoo_response(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_search_connector(monkeypatch, _RecordedResponse(RECORDED_SEARCH_RESPONSE))
    matches = asyncio.run(connector.search("apple", limit=5))
    assert [m.symbol for m in matches] == ["AAPL", "APLE"]
    top = matches[0]
    assert top.name == "Apple Inc."
    assert top.exchange == "NMS"
    assert top.currency == "USD"
    assert top.id == uuid5(INSTRUMENT_NS, "AAPL")


def test_search_skips_malformed_recorded_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_search_connector(monkeypatch, _RecordedResponse(RECORDED_SEARCH_RESPONSE))
    matches = asyncio.run(connector.search("apple", limit=5))
    # The symbol-less entry and the over-long junk symbol are dropped, not defaulted.
    assert all(m.symbol in {"AAPL", "APLE"} for m in matches)


def test_search_respects_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_search_connector(monkeypatch, _RecordedResponse(RECORDED_SEARCH_RESPONSE))
    assert len(asyncio.run(connector.search("apple", limit=1))) == 1


def test_search_returns_empty_on_provider_outage(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_search_connector(monkeypatch, httpx.ConnectError("recorded outage"))
    assert asyncio.run(connector.search("apple", limit=5)) == []


# --- quote -------------------------------------------------------------------


def test_quote_maps_recorded_info(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_connector(monkeypatch, lambda symbol: _RecordedTicker(RECORDED_AAPL_INFO))
    quote = asyncio.run(connector.quote("aapl"))
    assert quote.instrument.symbol == "AAPL"
    assert float(quote.price) == pytest.approx(233.25)
    assert float(quote.change) == pytest.approx(2.21)
    assert quote.change_percent is not None
    assert float(quote.change_percent) == pytest.approx(0.9566, abs=1e-3)
    assert quote.volume == 41_234_567
    assert quote.market_cap == 3_523_000_000_000
    assert quote.pe_ratio == Decimal("35.41")


def test_quote_meta_flags_source_and_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_connector(monkeypatch, lambda symbol: _RecordedTicker(RECORDED_AAPL_INFO))
    quote = asyncio.run(connector.quote("AAPL"))
    assert quote.meta.source == "yfinance"
    assert quote.meta.delayed is True
    assert quote.meta.availability == "available"


def test_quote_flags_partial_when_price_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded = {k: v for k, v in RECORDED_AAPL_INFO.items() if k not in {"currentPrice", "regularMarketPrice"}}
    connector = make_connector(monkeypatch, lambda symbol: _RecordedTicker(recorded))
    quote = asyncio.run(connector.quote("AAPL"))
    assert quote.price is None
    assert quote.change is None
    assert quote.meta.availability == "partial"


def test_quote_rejects_empty_provider_data(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_connector(monkeypatch, lambda symbol: _RecordedTicker({}))
    with pytest.raises(ConnectorUnavailable):
        asyncio.run(connector.quote("AAPL"))


def test_validate_uses_recorded_info(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_connector(monkeypatch, lambda symbol: _RecordedTicker(RECORDED_AAPL_INFO))
    assert asyncio.run(connector.validate("aapl")) is True


def test_validate_rejects_empty_info(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_connector(monkeypatch, lambda symbol: _RecordedTicker({}))
    assert asyncio.run(connector.validate("AAPL")) is False


# --- candles -----------------------------------------------------------------


def test_candles_map_recorded_history(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_connector(
        monkeypatch,
        lambda symbol: _RecordedTicker(RECORDED_AAPL_INFO, history=_RecordedHistory(RECORDED_HISTORY_ROWS)),
    )
    start = datetime(2026, 11, 24, tzinfo=timezone.utc)
    end = datetime(2026, 11, 26, tzinfo=timezone.utc)
    candles = asyncio.run(connector.candles("AAPL", start=start, end=end, interval="1d"))
    assert len(candles) == 2
    first = candles[0]
    assert first.timestamp == datetime(2026, 11, 24, 14, 30, tzinfo=timezone.utc)
    assert float(first.close) == pytest.approx(233.25)
    assert float(first.high) == pytest.approx(233.40)
    assert first.volume == 41_234_567


def test_candles_empty_history_returns_no_data(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_connector(
        monkeypatch, lambda symbol: _RecordedTicker(RECORDED_AAPL_INFO, history=_RecordedHistory([]))
    )
    start = datetime(2026, 11, 24, tzinfo=timezone.utc)
    end = datetime(2026, 11, 26, tzinfo=timezone.utc)
    assert asyncio.run(connector.candles("AAPL", start=start, end=end, interval="1d")) == []


# --- news ----------------------------------------------------------------------


def test_news_maps_both_recorded_shapes_and_skips_incomplete(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_connector(
        monkeypatch,
        lambda symbol: _RecordedTicker(RECORDED_AAPL_INFO, news=RECORDED_NEWS),
    )
    articles = asyncio.run(connector.news("AAPL", limit=10))
    assert [a.headline for a in articles] == [
        "Apple unveils new AI strategy",
        "Legacy headline from an older feed",
    ]
    top = articles[0]
    assert top.publisher == "Yahoo Finance"
    assert str(top.source_url) == "https://finance.yahoo.com/news/apple-unveils-ai-123456.html"
    assert top.published_at == datetime(2026, 11, 20, 18, 30, tzinfo=timezone.utc)
    assert top.sentiment == "unavailable"
    assert top.id == uuid5(NEWS_NS, "AAPL:Apple unveils new AI strategy")
    assert top.meta.source == "yfinance"
    assert top.meta.delayed is True
    assert articles[1].publisher == "Reuters"


def test_news_outage_raises_rather_than_defaulting(monkeypatch: pytest.MonkeyPatch) -> None:
    # The connector propagates provider outages instead of returning
    # fabricated or empty data; InstrumentService maps any such exception to
    # a clear "temporarily unavailable" response (or stale cache).
    connector = make_connector(monkeypatch, lambda symbol: _FailingTicker())
    with pytest.raises(RuntimeError, match="recorded provider outage"):
        asyncio.run(connector.news("AAPL", limit=10))


# --- beta ----------------------------------------------------------------------


def test_beta_uses_recorded_value(monkeypatch: pytest.MonkeyPatch) -> None:
    connector = make_connector(monkeypatch, lambda symbol: _RecordedTicker(RECORDED_AAPL_INFO))
    assert asyncio.run(connector.beta("AAPL")) == 1.24


def test_beta_fallback_is_documented_not_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    # The 1.0 fallback is a disclosed modelling assumption: it is listed in
    # the analysis `assumptions` output (services/analysis.py), so the API
    # flags it instead of silently defaulting.
    connector = make_connector(monkeypatch, lambda symbol: _FailingTicker())
    assert asyncio.run(connector.beta("AAPL")) == 1.0


# --- construction guard ---------------------------------------------------------


def test_missing_yfinance_dependency_is_a_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # None in sys.modules makes `import yfinance` fail, simulating the
    # library not being installed.
    monkeypatch.setitem(sys.modules, "yfinance", None)
    with pytest.raises(ConnectorUnavailable, match="yfinance is not installed"):
        YFinanceMarketDataConnector()
