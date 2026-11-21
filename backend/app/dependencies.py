from functools import lru_cache
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.market import DemoMarketDataConnector, MarketDataConnector, YFinanceMarketDataConnector
from app.core.config import get_settings
from app.core.database import get_session
from app.core.db import Database
from app.core.errors import BackendError
from app.core.security import decode_access_token
from app.models.user import User
from app.services.instruments import InstrumentService


@lru_cache
def get_market_connector() -> MarketDataConnector:
    settings = get_settings()
    if settings.market_data_provider.lower() == "yfinance":
        return YFinanceMarketDataConnector()
    return DemoMarketDataConnector()


@lru_cache
def get_instrument_service() -> InstrumentService:
    return InstrumentService(get_market_connector(), get_settings())


@lru_cache
def get_database() -> Database:
    return Database(get_settings().database_path)


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> UUID:
    if not authorization or not authorization.startswith("Bearer "):
        raise BackendError("authentication_required", "Authentication is required.", 401)
    user_id = decode_access_token(authorization[7:], get_settings().jwt_secret)
    exists = await session.scalar(select(User.id).where(User.id == user_id))
    if exists is None:
        raise BackendError("authentication_required", "Authentication is required.", 401)
    return user_id
