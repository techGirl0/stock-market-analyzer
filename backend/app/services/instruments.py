from datetime import datetime, timedelta, timezone

from app.connectors.market import ConnectorUnavailable, MarketDataConnector
from app.core.errors import BackendError
from app.schemas.v1 import Candle, InstrumentMatch, NewsArticle, Page, Quote


class InstrumentService:
    def __init__(self, connector: MarketDataConnector) -> None:
        self.connector = connector

    async def search(self, query: str, limit: int) -> Page[InstrumentMatch]:
        if not query.strip():
            return Page(items=[])
        try:
            items = await self.connector.search(query, limit=limit)
        except ConnectorUnavailable as exc:
            raise BackendError("provider_unavailable", str(exc), 503) from exc
        return Page(items=items)

    async def quote(self, symbol: str) -> Quote:
        try:
            if not await self.connector.validate(symbol):
                raise BackendError(
                    "ticker_not_found",
                    "The requested instrument was not recognised.",
                    404,
                )
            return await self.connector.quote(symbol)
        except BackendError:
            raise
        except ConnectorUnavailable as exc:
            raise BackendError("provider_unavailable", str(exc), 503) from exc
        except Exception as exc:
            raise BackendError(
                "provider_unavailable",
                "Market data is temporarily unavailable.",
                503,
            ) from exc

    async def candles(
        self, symbol: str, start: datetime | None, end: datetime | None, interval: str
    ) -> Page[Candle]:
        end = end or datetime.now(timezone.utc)
        start = start or end - timedelta(days=30)
        if start >= end:
            raise BackendError("validation_error", "start must be before end.", 422)
        try:
            if not await self.connector.validate(symbol):
                raise BackendError(
                    "ticker_not_found",
                    "The requested instrument was not recognised.",
                    404,
                )
            items = await self.connector.candles(
                symbol, start=start, end=end, interval=interval
            )
            return Page(items=items)
        except BackendError:
            raise
        except ConnectorUnavailable as exc:
            raise BackendError("provider_unavailable", str(exc), 503) from exc
        except Exception as exc:
            raise BackendError(
                "provider_unavailable",
                "Historical market data is temporarily unavailable.",
                503,
            ) from exc

    async def news(self, symbol: str, limit: int) -> Page[NewsArticle]:
        try:
            if not await self.connector.validate(symbol):
                raise BackendError(
                    "ticker_not_found",
                    "The requested instrument was not recognised.",
                    404,
                )
            return Page(items=await self.connector.news(symbol, limit=limit))
        except BackendError:
            raise
        except ConnectorUnavailable as exc:
            raise BackendError("provider_unavailable", str(exc), 503) from exc
        except Exception as exc:
            raise BackendError(
                "provider_unavailable",
                "News data is temporarily unavailable.",
                503,
            ) from exc
