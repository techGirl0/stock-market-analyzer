from functools import lru_cache

from app.connectors.market import DemoMarketDataConnector, MarketDataConnector, YFinanceMarketDataConnector
from app.core.config import get_settings
from app.services.instruments import InstrumentService
from app.core.db import Database
from app.core.security import decode_access_token
from fastapi import Header
from uuid import UUID
from app.core.errors import BackendError
from app.services.watchlists import WatchlistService


@lru_cache
def get_market_connector() -> MarketDataConnector:
    settings = get_settings()
    if settings.market_data_provider.lower() == "yfinance":
        return YFinanceMarketDataConnector()
    return DemoMarketDataConnector()


def get_instrument_service() -> InstrumentService:
    return InstrumentService(get_market_connector())


@lru_cache
def get_database() -> Database:
    return Database(get_settings().database_path)


def get_current_user(authorization: str | None = Header(default=None)) -> UUID:
    if not authorization or not authorization.startswith("Bearer "):
        raise BackendError("authentication_required", "Authentication is required.", 401)
    return decode_access_token(authorization[7:], get_settings().jwt_secret)


def get_watchlist_service() -> WatchlistService:
    return WatchlistService(get_database())
