from functools import lru_cache
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.llm import DisabledLLMConnector, GroqLLMConnector, LLMConnector
from app.connectors.market import DemoMarketDataConnector, MarketDataConnector, YFinanceMarketDataConnector
from app.core.config import get_settings
from app.core.database import get_session
from app.core.errors import BackendError
from app.core.security import decode_access_token
from app.models.user import User
from app.services.alerts import AlertService
from app.services.analysis import AnalysisService
from app.services.auth import AuthService
from app.services.instruments import InstrumentService
from app.services.news import NewsService
from app.services.portfolio import PortfolioService
from app.services.research import ResearchService
from app.services.watchlists import WatchlistService


@lru_cache
def get_market_connector() -> MarketDataConnector:
    settings = get_settings()
    if settings.market_data_provider.lower() == "yfinance":
        return YFinanceMarketDataConnector()
    return DemoMarketDataConnector()


@lru_cache
def get_instrument_service() -> InstrumentService:
    return InstrumentService(get_market_connector(), get_settings())


def get_llm_connector() -> LLMConnector:
    settings = get_settings()
    if settings.llm_provider.lower() == "groq":
        if not settings.groq_api_key:
            raise BackendError("llm_unavailable", "GROQ_API_KEY is not configured.", 503)
        return GroqLLMConnector(settings.groq_api_key, settings.groq_model)
    return DisabledLLMConnector()


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


async def get_watchlist_service(
    session: AsyncSession = Depends(get_session),
    instruments: InstrumentService = Depends(get_instrument_service),
) -> WatchlistService:
    return WatchlistService(session, instruments)


def get_analysis_service(
    instruments: InstrumentService = Depends(get_instrument_service),
) -> AnalysisService:
    return AnalysisService(instruments, get_llm_connector())


def get_research_service(
    instruments: InstrumentService = Depends(get_instrument_service),
) -> ResearchService:
    return ResearchService(instruments, get_llm_connector())


async def get_portfolio_service(
    session: AsyncSession = Depends(get_session),
    instruments: InstrumentService = Depends(get_instrument_service),
) -> PortfolioService:
    return PortfolioService(session, instruments)


async def get_alert_service(
    session: AsyncSession = Depends(get_session),
    instruments: InstrumentService = Depends(get_instrument_service),
) -> AlertService:
    return AlertService(session, instruments)


def get_news_service(
    instruments: InstrumentService = Depends(get_instrument_service),
) -> NewsService:
    return NewsService(instruments, get_llm_connector())


async def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    return AuthService(session, get_settings())
