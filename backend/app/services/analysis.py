from datetime import datetime, timezone

from app.connectors.llm import LLMConnector
from app.core.constants import DISCLAIMER
from app.schemas.analysis import AnalysisMeta, ForecastResponse, RiskProfile
from app.schemas.v1 import Availability
from app.services.finance import (
    compute_avg_dollar_volume,
    compute_max_drawdown,
    compute_scenarios,
    realized_volatility,
)
from app.services.instruments import InstrumentService
from app.services.snapshot import MIN_OBSERVATIONS, build_snapshot, year_closes

RISK_ASSUMPTIONS = [
    "At least 21 daily observations are required.",
    "Window: one year of daily closes (252 trading days).",
    "Beta benchmark: the broad market index (provider beta), fallback 1.0.",
]
FORECAST_ASSUMPTIONS = ["At least 21 daily observations are required.", "Ranges are not predictions."]


class AnalysisService:
    def __init__(self, instruments: InstrumentService, llm: LLMConnector) -> None:
        self.instruments = instruments
        self.llm = llm

    async def risk(self, symbol: str) -> RiskProfile:
        snap = await build_snapshot(self.instruments, self.llm, symbol)
        meta = AnalysisMeta(
            availability=Availability.available if snap.has_history else Availability.unavailable,
            calculated_at=datetime.now(timezone.utc),
            calculation_version="risk-v2",
            assumptions=RISK_ASSUMPTIONS,
            disclaimer=DISCLAIMER,
        )
        if not snap.has_history:
            return RiskProfile(score=None, components={}, meta=meta)

        score, components = snap.risk()
        # Display-only risk indicators (SCRUM-70): reported alongside the
        # composite score but not part of its weighted formula.
        components["Maximum Drawdown"] = f"{round(compute_max_drawdown(snap.closes) * 100, 1)}%"
        liquidity = compute_avg_dollar_volume(snap.closes, snap.volumes)
        components["Liquidity (Avg Daily $ Volume)"] = (
            f"${liquidity:,.0f}" if liquidity is not None else "Unavailable"
        )
        return RiskProfile(score=score, components=components, meta=meta)

    async def forecast(self, symbol: str, horizon: str) -> ForecastResponse:
        now = datetime.now(timezone.utc)
        closes, _volumes = await year_closes(self.instruments, symbol)

        def meta(available: bool) -> AnalysisMeta:
            return AnalysisMeta(
                availability=Availability.available if available else Availability.unavailable,
                calculated_at=now,
                calculation_version="forecast-v2",
                assumptions=FORECAST_ASSUMPTIONS,
                disclaimer=DISCLAIMER,
            )

        vol = realized_volatility(closes) if len(closes) >= MIN_OBSERVATIONS else None
        if vol is None:
            return ForecastResponse(horizon=horizon, scenarios=[], meta=meta(False))

        _daily, annual_vol = vol
        scenarios = compute_scenarios(closes[-1], annual_vol, [horizon])
        numeric_scenarios = [s.model_dump(exclude={"label"}) for s in scenarios]
        return ForecastResponse(horizon=horizon, scenarios=numeric_scenarios, meta=meta(True))
