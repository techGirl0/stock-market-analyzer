import logging
from datetime import datetime, timezone
from math import sqrt

from app.connectors.llm import LLMConnector
from app.connectors.market import MarketDataConnector
from app.core.constants import DISCLAIMER
from app.schemas.analysis import AnalysisMeta, ForecastResponse, RiskProfile
from app.schemas.v1 import Availability
from app.services.finance import (
    compute_avg_dollar_volume,
    compute_max_drawdown,
    compute_risk_score,
    compute_scenarios,
    fetch_beta,
    resolve_horizon_days,
)

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, market: MarketDataConnector, llm: LLMConnector | None = None) -> None:
        self.market = market
        self.llm = llm

    async def risk(self, symbol: str) -> RiskProfile:
        now = datetime.now(timezone.utc)
        if not await self.market.validate(symbol):
            from app.core.errors import BackendError
            raise BackendError("ticker_not_found", "The requested instrument was not recognised.", 404)

        candles = await self.market.candles(symbol, start=now.replace(year=now.year - 1), end=now, interval="1d")
        meta = AnalysisMeta(
            availability=Availability.available if len(candles) >= 21 else Availability.unavailable,
            calculated_at=now,
            calculation_version="risk-v2",
            assumptions=[
                "At least 21 daily observations are required.",
                "Window: one year of daily closes (252 trading days).",
                "Beta benchmark: the broad market index (yfinance beta), fallback 1.0.",
            ],
            disclaimer=DISCLAIMER,
        )
        if len(candles) < 21:
            return RiskProfile(score=None, components={}, meta=meta)

        prices = [float(c.close) for c in candles]
        volumes = [c.volume for c in candles]
        returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
        mean = sum(returns) / len(returns)
        variance = sum((v - mean) ** 2 for v in returns) / (len(returns) - 1)
        daily_vol = sqrt(variance)
        annual_vol = daily_vol * sqrt(252) * 100

        low_52w = min(prices)
        high_52w = max(prices)
        current = prices[-1]
        pos_52w = (current - low_52w) / (high_52w - low_52w) if high_52w > low_52w else 0.5

        beta = await fetch_beta(symbol)

        news_sentiment: float | None = None
        if self.llm is not None:
            try:
                articles = await self.market.news(symbol, limit=10)
                headlines = [a.headline for a in articles if a.headline]
                if headlines:
                    news_sentiment = await self.llm.sentiment_score(symbol, headlines)
            except Exception:
                logger.warning("News sentiment fetch failed for %s", symbol)

        score, components = compute_risk_score(
            annual_vol=annual_vol,
            beta=beta,
            pos_52w=pos_52w,
            news_sentiment=news_sentiment,
        )
        # Display-only risk indicators (SCRUM-70): reported alongside the
        # composite score but not part of its weighted formula.
        components["Maximum Drawdown"] = f"{round(compute_max_drawdown(prices) * 100, 1)}%"
        liquidity = compute_avg_dollar_volume(prices, volumes)
        components["Liquidity (Avg Daily $ Volume)"] = (
            f"${liquidity:,.0f}" if liquidity is not None else "Unavailable"
        )

        return RiskProfile(score=score, components=components, meta=meta)

    async def forecast(self, symbol: str, horizon: str) -> ForecastResponse:
        now = datetime.now(timezone.utc)
        if not await self.market.validate(symbol):
            from app.core.errors import BackendError
            raise BackendError("ticker_not_found", "The requested instrument was not recognised.", 404)

        candles = await self.market.candles(symbol, start=now.replace(year=now.year - 1), end=now, interval="1d")
        unavail_meta = AnalysisMeta(
            availability=Availability.unavailable,
            calculated_at=now,
            calculation_version="forecast-v2",
            assumptions=["At least 21 daily observations are required.", "Ranges are not predictions."],
            disclaimer=DISCLAIMER,
        )
        if len(candles) < 21:
            return ForecastResponse(horizon=horizon, scenarios=[], meta=unavail_meta)

        prices = [float(c.close) for c in candles]
        returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
        mean_r = sum(returns) / len(returns)
        variance = sum((v - mean_r) ** 2 for v in returns) / (len(returns) - 1)
        daily_vol = sqrt(variance)
        annual_vol = daily_vol * sqrt(252)
        current_price = prices[-1]

        days = resolve_horizon_days(horizon)
        scenarios = compute_scenarios(current_price, annual_vol, [horizon], days_override=days)
        numeric_scenarios = [{k: v for k, v in s.items() if k != "label"} for s in scenarios]

        return ForecastResponse(
            horizon=horizon,
            scenarios=numeric_scenarios,
            meta=AnalysisMeta(
                availability=Availability.available,
                calculated_at=now,
                calculation_version="forecast-v2",
                assumptions=["At least 21 daily observations are required.", "Ranges are not predictions."],
                disclaimer=DISCLAIMER,
            ),
        )
