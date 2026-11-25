from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Protocol, cast
from uuid import UUID, uuid5

import httpx
from pydantic import AnyHttpUrl

from app.schemas.v1 import (
    Availability,
    Candle,
    DataMeta,
    InstrumentMatch,
    NewsArticle,
    Quote,
    normalize_symbol,
)


class ConnectorUnavailable(Exception):
    """Raised when an external provider cannot supply data."""


class MarketDataConnector(Protocol):
    async def search(self, query: str, *, limit: int) -> list[InstrumentMatch]: ...
    async def validate(self, symbol: str) -> bool: ...
    async def quote(self, symbol: str) -> Quote: ...
    async def candles(
        self, symbol: str, *, start: datetime, end: datetime, interval: str
    ) -> list[Candle]: ...

    async def news(self, symbol: str, *, limit: int) -> list[NewsArticle]: ...


class DemoMarketDataConnector:
    """Deterministic local connector used until a licensed provider is configured."""

    _known = {
        "AAPL": ("Apple Inc.", "NASDAQ"),
        "MSFT": ("Microsoft Corporation", "NASDAQ"),
        "TSLA": ("Tesla, Inc.", "NASDAQ"),
        "AMZN": ("Amazon.com, Inc.", "NASDAQ"),
        "GOOGL": ("Alphabet Inc.", "NASDAQ"),
        "NVDA": ("NVIDIA Corporation", "NASDAQ"),
    }

    def _instrument(self, symbol: str) -> InstrumentMatch:
        symbol = normalize_symbol(symbol)
        name, exchange = self._known[symbol]
        return InstrumentMatch(
            id=uuid5(UUID("00000000-0000-0000-0000-000000000001"), symbol),
            symbol=symbol,
            name=name,
            exchange=exchange,
            currency="USD",
        )

    async def search(self, query: str, *, limit: int) -> list[InstrumentMatch]:
        normalized = query.strip().upper()
        if not normalized:
            return []
        return [
            self._instrument(symbol)
            for symbol, (name, _) in self._known.items()
            if normalized in symbol or normalized in name.upper()
        ][:limit]

    async def validate(self, symbol: str) -> bool:
        return normalize_symbol(symbol) in self._known

    async def quote(self, symbol: str) -> Quote:
        instrument = self._instrument(symbol)
        now = datetime.now(timezone.utc)
        price = Decimal(100 + len(instrument.symbol))
        return Quote(
            instrument=instrument,
            price=price,
            previous_close=price - 1,
            change=Decimal(1),
            change_percent=(Decimal(100) / (price - Decimal(1))).quantize(Decimal("0.0001")),
            volume=1_000_000,
            as_of=now,
            meta=DataMeta(
                source="demo",
                fetched_at=now,
                availability=Availability.available,
                delayed=True,
            ),
        )

    async def candles(
        self, symbol: str, *, start: datetime, end: datetime, interval: str
    ) -> list[Candle]:
        if not await self.validate(symbol):
            return []
        points = []
        base = Decimal("100.0")
        for day in range(30):
            timestamp = start + timedelta(days=day)
            if timestamp > end:
                break
            close = base + Decimal(day % 5) * Decimal("0.8") - Decimal(day % 3) * Decimal("0.2")
            points.append(
                Candle(
                    timestamp=timestamp,
                    open=close - Decimal("0.5"),
                    high=close + Decimal(1),
                    low=close - Decimal(1),
                    close=close,
                    volume=100_000 + day,
                )
            )
        return points

    async def news(self, symbol: str, *, limit: int) -> list[NewsArticle]:
        if not await self.validate(symbol):
            return []
        now = datetime.now(timezone.utc)
        return [
            NewsArticle(
                id=uuid5(UUID("00000000-0000-0000-0000-000000000002"), symbol),
                headline=f"{normalize_symbol(symbol)} market data demo item",
                publisher="WolfStreet Signal Demo",
                published_at=now,
                source_url=cast(AnyHttpUrl, "https://example.com/market-data-demo"),
                summary="Demo content used for local API development.",
                sentiment="unavailable",
                meta=DataMeta(
                    source="demo",
                    fetched_at=now,
                    availability=Availability.available,
                    delayed=True,
                ),
            )
        ][:limit]


class YFinanceMarketDataConnector:
    """Optional adapter boundary for the existing yfinance prototype."""

    def __init__(self) -> None:
        try:
            import yfinance  # type: ignore
        except ImportError as exc:
            raise ConnectorUnavailable(
                "yfinance is not installed; use MARKET_DATA_PROVIDER=demo"
            ) from exc
        self._yfinance = yfinance

    async def search(self, query: str, *, limit: int) -> list[InstrumentMatch]:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {"q": query, "quotesCount": limit, "newsCount": 0, "listsCount": 0}
        headers = {"User-Agent": "stock-market-analyzer/1.0"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                quotes = resp.json().get("quotes", [])
        except Exception:
            return []
        results: list[InstrumentMatch] = []
        for item in quotes:
            symbol = item.get("symbol")
            if not symbol:
                continue
            try:
                symbol = normalize_symbol(symbol)
            except ValueError:
                continue
            results.append(
                InstrumentMatch(
                    id=uuid5(UUID("00000000-0000-0000-0000-000000000001"), symbol),
                    symbol=symbol,
                    name=item.get("longname") or item.get("shortname") or symbol,
                    exchange=item.get("exchange"),
                    currency=item.get("currency"),
                )
            )
        return results[:limit]

    async def validate(self, symbol: str) -> bool:
        normalized = normalize_symbol(symbol)
        info = self._yfinance.Ticker(normalized).info
        return bool(info.get("quoteType") or info.get("shortName"))

    async def quote(self, symbol: str) -> Quote:
        normalized = normalize_symbol(symbol)
        ticker = self._yfinance.Ticker(normalized)
        info = ticker.info
        if not info or not (info.get("quoteType") or info.get("shortName")):
            raise ConnectorUnavailable("market data provider returned no instrument")
        now = datetime.now(timezone.utc)
        current = info.get("currentPrice") or info.get("regularMarketPrice")
        previous = info.get("previousClose")
        raw_pe = info.get("trailingPE")
        return Quote(
            instrument=InstrumentMatch(
                id=uuid5(UUID("00000000-0000-0000-0000-000000000001"), normalized),
                symbol=normalized,
                name=info.get("longName") or info.get("shortName") or normalized,
                exchange=info.get("exchange"),
                currency=info.get("currency"),
            ),
            price=current,
            previous_close=previous,
            change=(current - previous) if current is not None and previous is not None else None,
            change_percent=(
                ((current - previous) / previous * 100)
                if current is not None and previous not in (None, 0)
                else None
            ),
            volume=info.get("regularMarketVolume"),
            as_of=now,
            market_cap=info.get("marketCap"),
            pe_ratio=Decimal(str(round(float(raw_pe), 2))) if raw_pe is not None else None,
            meta=DataMeta(
                source="yfinance",
                fetched_at=now,
                availability=Availability.available if current is not None else Availability.partial,
                delayed=True,
            ),
        )

    async def candles(
        self, symbol: str, *, start: datetime, end: datetime, interval: str
    ) -> list[Candle]:
        normalized = normalize_symbol(symbol)
        history = self._yfinance.Ticker(normalized).history(
            start=start, end=end, interval=interval
        )
        return [
            Candle(
                timestamp=index.to_pydatetime().astimezone(timezone.utc),
                open=row["Open"],
                high=row["High"],
                low=row["Low"],
                close=row["Close"],
                volume=int(row["Volume"]) if row["Volume"] is not None else None,
            )
            for index, row in history.iterrows()
        ]

    async def news(self, symbol: str, *, limit: int) -> list[NewsArticle]:
        # yfinance news has changed shape across releases. Keep normalization
        # in this adapter and expose unavailable sentiment until a sentiment
        # service is configured.
        normalized = normalize_symbol(symbol)
        now = datetime.now(timezone.utc)
        raw_items = self._yfinance.Ticker(normalized).news or []
        results: list[NewsArticle] = []
        for item in raw_items[:limit]:
            content = item.get("content", item)
            title = content.get("title")
            if not title:
                continue
            published = content.get("pubDate") or content.get("displayTime")
            url = content.get("canonicalUrl", {}).get("url") or content.get("link")
            if not url or not published:
                continue
            results.append(
                NewsArticle(
                    id=uuid5(
                        UUID("00000000-0000-0000-0000-000000000002"),
                        f"{normalized}:{title}",
                    ),
                    headline=title,
                    publisher=content.get("provider", {}).get("displayName"),
                    published_at=published,
                    source_url=url,
                    summary=None,
                    sentiment="unavailable",
                    meta=DataMeta(
                        source="yfinance",
                        fetched_at=now,
                        availability=Availability.available,
                        delayed=True,
                    ),
                )
            )
        return results
