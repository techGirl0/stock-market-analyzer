"""Shared test fakes: one LLM fake and one market-data fake family.

Every test that needs a deterministic LLM or market provider uses these
instead of hand-rolling a new duck type per file.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4, uuid5

from app.connectors.market import (
    INSTRUMENT_NS,
    ConnectorUnavailable,
    DemoMarketDataConnector,
    MarketDataConnector,
)
from app.schemas.v1 import (
    Availability,
    Candle,
    DataMeta,
    Instrument,
    InstrumentMatch,
    NewsArticle,
    Quote,
)
from app.services.instruments import InstrumentService


class FakeLLM:
    """Deterministic LLM connector returning canned responses."""

    def __init__(
        self,
        brief_text: str = "FAKE_BRIEF",
        chat_reply: str = "FAKE_CHAT",
        sentiment: float | None = None,
        explain_text: str = "FAKE_EXPLANATION",
    ) -> None:
        self.brief_text = brief_text
        self.chat_reply = chat_reply
        self.sentiment = sentiment
        self.explain_text = explain_text
        self.calls: list[str] = []

    async def brief(self, ticker: str, context: str) -> str:
        self.calls.append("brief")
        return self.brief_text

    async def chat(self, ticker: str, context: str, messages: list) -> str:
        self.calls.append("chat")
        return self.chat_reply

    async def sentiment_score(self, ticker: str, headlines: list[str]) -> float | None:
        self.calls.append("sentiment_score")
        return self.sentiment

    async def news_feed(self, ticker: str, headlines: list[str]) -> list[dict]:
        self.calls.append("news_feed")
        return [{"headline": h, "sentiment": "NEUTRAL", "reason": "fake"} for h in headlines]

    async def explain_risk(self, ticker: str, context: str) -> str:
        self.calls.append("explain_risk")
        return self.explain_text

    async def explain_volatility(self, ticker: str, context: str) -> str:
        self.calls.append("explain_volatility")
        return self.explain_text

    async def explain_scenarios(self, ticker: str, context: str) -> str:
        self.calls.append("explain_scenarios")
        return self.explain_text


class EchoUserFakeLLM(FakeLLM):
    """Echoes the last user message — lets tests inspect what reached the LLM."""

    def __init__(self) -> None:
        super().__init__()

    async def chat(self, ticker: str, context: str, messages: list) -> str:
        self.calls.append("chat")
        return messages[-1].content


class FixedSeriesConnector(MarketDataConnector):
    """Deterministic connector: fixed candles, one news article, fixed beta."""

    def __init__(self, closes: list[float], volumes: list[int] | None = None, beta: float = 1.0) -> None:
        self._closes = closes
        self._volumes = volumes if volumes is not None else [10_000] * len(closes)
        self._beta = beta

    async def search(self, query: str, *, limit: int) -> list[InstrumentMatch]:
        return []

    async def validate(self, symbol: str) -> bool:
        return symbol == "TEST"

    async def quote(self, symbol: str) -> Quote:
        now = datetime.now(timezone.utc)
        price = Decimal(str(self._closes[-1])) if self._closes else None
        return Quote(
            instrument=InstrumentMatch(
                id=uuid5(INSTRUMENT_NS, symbol),
                symbol=symbol,
                name=f"{symbol} test instrument",
                exchange="TEST",
                currency="USD",
            ),
            price=price,
            as_of=now,
            meta=DataMeta(source="fixed", fetched_at=now, availability=Availability.available, delayed=False),
        )

    async def candles(self, symbol: str, *, start: datetime, end: datetime, interval: str) -> list[Candle]:
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        return [
            Candle(
                timestamp=base.replace(day=(i % 28) + 1, month=(i // 28) + 1),
                open=Decimal(str(c)),
                high=Decimal(str(c)),
                low=Decimal(str(c)),
                close=Decimal(str(c)),
                volume=v,
            )
            for i, (c, v) in enumerate(zip(self._closes, self._volumes))
        ]

    async def news(self, symbol: str, *, limit: int) -> list[NewsArticle]:
        now = datetime.now(timezone.utc)
        return [
            NewsArticle(
                id=uuid5(INSTRUMENT_NS, f"{symbol}:news"),
                headline="Test headline one",
                publisher="Test Publisher",
                published_at=now,
                source_url="https://example.com/news",  # type: ignore[arg-type]
                summary=None,
                sentiment="unavailable",
                meta=DataMeta(source="fixed", fetched_at=now, availability=Availability.available, delayed=False),
            )
        ]

    async def beta(self, symbol: str) -> float:
        return self._beta


class ShortHistoryDemoConnector(DemoMarketDataConnector):
    """Only 5 candles — below the 21-candle threshold for vol/risk/scenarios."""

    async def candles(self, symbol, *, start, end, interval):  # type: ignore[override]
        full = await super().candles(symbol, start=start, end=end, interval=interval)
        return full[:5]


class NoNewsDemoConnector(DemoMarketDataConnector):
    """No news articles for any symbol."""

    async def news(self, symbol, *, limit):  # type: ignore[override]
        return []


class NoPriceDemoConnector(DemoMarketDataConnector):
    """Quote with no price and no candles — simulates data unavailable."""

    async def quote(self, symbol):  # type: ignore[override]
        q = await super().quote(symbol)
        return q.model_copy(update={"price": None, "change": None, "change_percent": None})

    async def candles(self, symbol, *, start, end, interval):  # type: ignore[override]
        return []


class StaleQuoteDemoConnector(DemoMarketDataConnector):
    """Quote marked stale — simulates delayed/stale market data."""

    async def quote(self, symbol):  # type: ignore[override]
        q = await super().quote(symbol)
        stale_meta = DataMeta(
            source="demo",
            fetched_at=q.meta.fetched_at,
            availability=Availability.stale,
            delayed=True,
        )
        return q.model_copy(update={"meta": stale_meta})


class ProviderDownConnector(DemoMarketDataConnector):
    """Every provider call fails — simulates an outage."""

    async def validate(self, symbol):  # type: ignore[override]
        raise ConnectorUnavailable("provider is down")

    async def quote(self, symbol):  # type: ignore[override]
        raise ConnectorUnavailable("provider is down")

    async def candles(self, symbol, *, start, end, interval):  # type: ignore[override]
        raise ConnectorUnavailable("provider is down")

    async def news(self, symbol, *, limit):  # type: ignore[override]
        raise ConnectorUnavailable("provider is down")


class _FixedQuoteConnector(DemoMarketDataConnector):
    """Connector that returns one fixed quote (or raises) for every symbol."""

    def __init__(self, quote: Quote | None = None, error: Exception | None = None) -> None:
        self._quote = quote
        self._error = error
        self.quote_calls = 0

    async def quote(self, symbol: str):  # type: ignore[override]
        self.quote_calls += 1
        if self._error is not None:
            raise self._error
        assert self._quote is not None
        return self._quote


class StubInstrumentService(InstrumentService):
    """InstrumentService wired to a single fixed quote.

    verify_symbol and every other behaviour come from the real service, so
    the stub cannot drift from production.
    """

    def __init__(self, quote: Quote | None = None, error: Exception | None = None) -> None:
        self._stub = _FixedQuoteConnector(quote, error)
        super().__init__(self._stub)

    @property
    def quote_calls(self) -> int:
        return self._stub.quote_calls


def fixed_quote(symbol: str = "AAPL", price: float | None = 150.0) -> Quote:
    now = datetime.now(timezone.utc)
    return Quote(
        instrument=Instrument(id=uuid4(), symbol=symbol, name=symbol),
        price=Decimal(str(price)) if price is not None else None,
        as_of=now,
        meta=DataMeta(source="demo", fetched_at=now, availability=Availability.available, delayed=False),
    )


def unavailable_quote(symbol: str = "AAPL") -> Quote:
    now = datetime.now(timezone.utc)
    return Quote(
        instrument=Instrument(id=uuid4(), symbol=symbol, name=symbol),
        price=None,
        as_of=now,
        meta=DataMeta(source="demo", fetched_at=now, availability=Availability.unavailable, delayed=False),
    )
