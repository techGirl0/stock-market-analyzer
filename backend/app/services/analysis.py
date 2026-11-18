from datetime import datetime, timezone
from math import exp, sqrt
from app.connectors.market import MarketDataConnector
from app.schemas.analysis import AnalysisMeta, ForecastResponse, RiskProfile
from app.schemas.v1 import Availability

DISCLAIMER = "Statistical analysis is uncertain and is not financial advice."

class AnalysisService:
    def __init__(self, market: MarketDataConnector) -> None:
        self.market = market

    async def risk(self, symbol: str) -> RiskProfile:
        now = datetime.now(timezone.utc)
        if not await self.market.validate(symbol):
            from app.core.errors import BackendError
            raise BackendError("ticker_not_found", "The requested instrument was not recognised.", 404)
        candles = await self.market.candles(symbol, start=now.replace(year=now.year - 1), end=now, interval="1d")
        meta = AnalysisMeta(availability=Availability.available if len(candles) >= 21 else Availability.unavailable,
            calculated_at=now, calculation_version="risk-v1", assumptions=["At least 21 daily observations are required."],
            disclaimer=DISCLAIMER)
        if len(candles) < 21:
            return RiskProfile(score=None, components={}, meta=meta)
        returns = [
            float(candles[index].close / candles[index - 1].close - 1)
            for index in range(1, len(candles))
        ]
        mean = sum(returns) / len(returns)
        variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1)
        volatility = sqrt(variance) * sqrt(252) * 100
        score = min(10, max(1, round(2 + volatility / 10)))
        return RiskProfile(
            score=score,
            components={"annualized_volatility_percent": round(volatility, 2)},
            meta=meta,
        )

    async def forecast(self, symbol: str, horizon: str) -> ForecastResponse:
        now = datetime.now(timezone.utc)
        if not await self.market.validate(symbol):
            from app.core.errors import BackendError
            raise BackendError("ticker_not_found", "The requested instrument was not recognised.", 404)
        candles = await self.market.candles(symbol, start=now.replace(year=now.year - 1), end=now, interval="1d")
        if len(candles) < 21:
            return ForecastResponse(
                horizon=horizon, scenarios=[],
                meta=AnalysisMeta(
                    availability=Availability.unavailable,
                    calculated_at=now, calculation_version="forecast-v1",
                    assumptions=["At least 21 daily observations are required.", "Ranges are not predictions."],
                    disclaimer=DISCLAIMER,
                ),
            )
        prices = [float(candle.close) for candle in candles]
        returns = [prices[index] / prices[index - 1] - 1 for index in range(1, len(prices))]
        mean = sum(returns) / len(returns)
        variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1)
        daily_volatility = sqrt(variance)
        days = int(horizon.rstrip("d")) if horizon.endswith("d") else 20
        expected = prices[-1] * exp(mean * days)
        spread = prices[-1] * daily_volatility * sqrt(days)
        return ForecastResponse(
            horizon=horizon,
            scenarios=[{
                "lower": round(max(0, expected - spread), 2),
                "expected": round(expected, 2),
                "upper": round(expected + spread, 2),
            }],
            meta=AnalysisMeta(
                availability=Availability.available,
                calculated_at=now, calculation_version="forecast-v1",
                assumptions=["At least 21 daily observations are required.", "Ranges are not predictions."],
                disclaimer=DISCLAIMER,
            ),
        )
