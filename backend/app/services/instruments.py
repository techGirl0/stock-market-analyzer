from datetime import datetime, timedelta, timezone
from time import monotonic

from app.connectors.market import ConnectorUnavailable, MarketDataConnector
from app.core.errors import BackendError
from app.schemas.v1 import (
    Availability,
    Candle,
    DataMeta,
    HistoryResponse,
    InstrumentMatch,
    NewsArticle,
    Page,
    Quote,
)


class InstrumentService:
    def __init__(self, connector: MarketDataConnector, settings=None, clock=monotonic) -> None:
        self.connector = connector
        self.settings = settings
        self.clock = clock
        self._cache: dict[tuple[str, str], tuple[float, object]] = {}
        self._budget_started = clock()
        self._budget_used = 0

    def _setting(self, name: str, default: int) -> int:
        return int(getattr(self.settings, name, default))

    def _cached(self, key: tuple[str, str]) -> tuple[object | None, bool]:
        entry = self._cache.get(key)
        if entry is None:
            return None, False
        age = self.clock() - entry[0]
        return entry[1], age <= self._setting("provider_cache_seconds", 60)

    def _store(self, key: tuple[str, str], value: object) -> None:
        self._cache[key] = (self.clock(), value)

    def _budget(self) -> None:
        now = self.clock()
        window = self._setting("provider_budget_window_seconds", 60)
        if now - self._budget_started >= window:
            self._budget_started, self._budget_used = now, 0
        if self._budget_used >= self._setting("provider_request_budget", 60):
            raise BackendError(
                "provider_rate_limited",
                "Market data provider request budget is exhausted.",
                429,
            )
        self._budget_used += 1

    async def search(self, query: str, limit: int) -> Page[InstrumentMatch]:
        if not query.strip():
            return Page(items=[])
        try:
            items = await self.connector.search(query, limit=limit)
        except ConnectorUnavailable as exc:
            raise BackendError("provider_unavailable", str(exc), 503) from exc
        return Page(items=items)

    async def quote(self, symbol: str) -> Quote:
        key = ("quote", symbol.strip().upper())
        cached, fresh = self._cached(key)
        if fresh and isinstance(cached, Quote):
            return cached
        try:
            self._budget()
            if not await self.connector.validate(symbol):
                raise BackendError(
                    "ticker_not_found",
                    "The requested instrument was not recognised.",
                    404,
                )
            result = await self.connector.quote(symbol)
            self._store(key, result)
            return result
        except BackendError:
            raise
        except ConnectorUnavailable as exc:
            stale, _ = self._cached(key)
            if isinstance(stale, Quote) and self.clock() - self._cache[key][0] <= self._setting("provider_max_stale_seconds", 300):
                return stale.model_copy(
                    update={"meta": stale.meta.model_copy(update={"availability": Availability.stale})}
                )
            raise BackendError("provider_unavailable", str(exc), 503) from exc
        except Exception as exc:
            stale, _ = self._cached(key)
            if isinstance(stale, Quote) and self.clock() - self._cache[key][0] <= self._setting("provider_max_stale_seconds", 300):
                return stale.model_copy(
                    update={"meta": stale.meta.model_copy(update={"availability": Availability.stale})}
                )
            raise BackendError(
                "provider_unavailable",
                "Market data is temporarily unavailable.",
                503,
            ) from exc

    async def candles(
        self,
        symbol: str,
        start: datetime | None,
        end: datetime | None,
        interval: str,
        limit: int = 100,
    ) -> Page[Candle]:
        end = end or datetime.now(timezone.utc)
        start = start or end - timedelta(days=30)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        else:
            start = start.astimezone(timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        else:
            end = end.astimezone(timezone.utc)
        if start >= end:
            raise BackendError("validation_error", "start must be before end.", 422)
        key = ("candles", f"{symbol.strip().upper()}:{start.isoformat()}:{end.isoformat()}:{interval}")
        cached, fresh = self._cached(key)
        if fresh and isinstance(cached, Page):
            return cached
        try:
            self._budget()
            if not await self.connector.validate(symbol):
                raise BackendError(
                    "ticker_not_found",
                    "The requested instrument was not recognised.",
                    404,
                )
            items = await self.connector.candles(
                symbol, start=start, end=end, interval=interval
            )
            fetched_at = datetime.now(timezone.utc)
            result = Page(
                items=items[:limit],
                meta=DataMeta(
                    source=type(self.connector).__name__,
                    fetched_at=fetched_at,
                    availability=Availability.available,
                    delayed=True,
                ),
            )
            self._store(key, result)
            return result
        except BackendError:
            raise
        except ConnectorUnavailable as exc:
            stale, _ = self._cached(key)
            if isinstance(stale, Page) and self.clock() - self._cache[key][0] <= self._setting("provider_max_stale_seconds", 300):
                return stale.model_copy(
                    update={"meta": stale.meta.model_copy(update={"availability": Availability.stale})}
                )
            raise BackendError("provider_unavailable", str(exc), 503) from exc
        except Exception as exc:
            stale, _ = self._cached(key)
            if isinstance(stale, Page) and self.clock() - self._cache[key][0] <= self._setting("provider_max_stale_seconds", 300):
                return stale.model_copy(
                    update={"meta": stale.meta.model_copy(update={"availability": Availability.stale})}
                )
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

    async def history(
        self,
        symbol: str,
        start: datetime | None,
        end: datetime | None,
        interval: str,
        limit: int,
    ) -> HistoryResponse:
        page = await self.candles(symbol, start, end, interval, limit)
        if page.meta is None:
            raise BackendError(
                "provider_unavailable",
                "Historical market data is temporarily unavailable.",
                503,
            )
        return HistoryResponse(
            items=page.items,
            source=page.meta.source,
            delayed=page.meta.delayed,
            availability=page.meta.availability,
            fetched_at=page.meta.fetched_at,
        )
