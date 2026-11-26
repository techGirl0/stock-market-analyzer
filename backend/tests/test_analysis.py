"""
SCRUM-70: deterministic unit tests for AnalysisService with a fixed price
series and a fake provider. No network calls; no API key required.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.connectors.market import MarketDataConnector
from app.core.errors import BackendError
from app.schemas.v1 import Candle
from app.services.analysis import AnalysisService
from app.services.finance import compute_avg_dollar_volume, compute_max_drawdown


class FixedSeriesConnector(MarketDataConnector):
    """Deterministic market connector: fixed candles, no news."""

    def __init__(self, closes: list[float], volumes: list[int] | None = None) -> None:
        self._closes = closes
        self._volumes = volumes if volumes is not None else [10_000] * len(closes)

    async def search(self, query: str, limit: int = 10):
        return []

    async def validate(self, symbol: str) -> bool:
        return symbol == "TEST"

    async def quote(self, symbol: str):
        raise BackendError("provider_unavailable", "not needed in these tests", 503)

    async def candles(self, symbol: str, *, start, end, interval: str = "1d"):
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

    async def news(self, symbol: str, *, limit: int = 10):
        return [_Headline("Test headline one"), _Headline("Test headline two")]


class _Headline:
    def __init__(self, headline: str) -> None:
        self.headline = headline


class FakeSentimentLLM:
    async def sentiment_score(self, ticker: str, headlines: list[str]) -> float:
        return 0.8


def _service(closes: list[float], volumes: list[int] | None = None) -> AnalysisService:
    return AnalysisService(FixedSeriesConnector(closes, volumes), FakeSentimentLLM())


@pytest.mark.asyncio
async def test_risk_known_values(monkeypatch):
    monkeypatch.setattr("app.services.analysis.fetch_beta", _fake_beta)
    # 30 rising closes with one dip: peak 110 -> trough 99 = -10% drawdown.
    closes = [100.0 + (i % 3) * 5.0 for i in range(30)]
    closes[10] = 110.0
    closes[11] = 99.0
    service = _service(closes, volumes=[1_000] * 30)

    result = await service.risk("TEST")

    assert result.meta.availability == "available"
    assert result.score is not None and 1 <= result.score <= 10
    assert "Maximum Drawdown" in result.components
    assert result.components["Maximum Drawdown"] == "-10.0%"
    expected_liquidity = sum(c * 1_000 for c in closes) / len(closes)
    assert result.components["Liquidity (Avg Daily $ Volume)"] == f"${expected_liquidity:,.0f}"
    assert result.components["Beta vs Market"] == 1.25
    assert result.components["News Sentiment"] == 0.8
    # window and benchmark documented in the response
    assert any("Window" in a for a in result.meta.assumptions)
    assert any("Beta benchmark" in a for a in result.meta.assumptions)


async def _fake_beta(symbol: str) -> float:
    return 1.25


@pytest.mark.asyncio
async def test_risk_unavailable_below_21_observations(monkeypatch):
    monkeypatch.setattr("app.services.analysis.fetch_beta", _fake_beta)
    result = await _service([100.0] * 10).risk("TEST")
    assert result.score is None
    assert result.components == {}
    assert result.meta.availability == "unavailable"


@pytest.mark.asyncio
async def test_risk_unknown_ticker_raises_404():
    with pytest.raises(BackendError) as exc_info:
        await _service([100.0] * 30).risk("NOPE")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_forecast_deterministic(monkeypatch):
    monkeypatch.setattr("app.services.analysis.fetch_beta", _fake_beta)
    service = _service([100.0 + (i % 5) for i in range(60)])
    first = await service.forecast("TEST", "1m")
    second = await service.forecast("TEST", "1m")
    # calculated_at is a wall-clock timestamp; the numbers must be identical
    assert first.scenarios == second.scenarios, "same input must produce identical output"
    assert first.horizon == second.horizon


@pytest.mark.asyncio
async def test_forecast_short_horizons(monkeypatch):
    monkeypatch.setattr("app.services.analysis.fetch_beta", _fake_beta)
    service = _service([100.0 + (i % 5) for i in range(60)])

    week = await service.forecast("TEST", "1w")
    month = await service.forecast("TEST", "1m")
    quarter = await service.forecast("TEST", "3m")

    assert week.meta.availability == month.meta.availability == quarter.meta.availability == "available"
    # longer horizons must widen the range: bull - bear grows with the horizon
    def spread(resp):
        s = resp.scenarios[0]
        return s["bull"] - s["bear"]

    assert spread(week) < spread(month) < spread(quarter)
    # ranges, never a single price target
    for resp in (week, month, quarter):
        s = resp.scenarios[0]
        assert s["bear"] < s["base"] < s["bull"]


@pytest.mark.asyncio
async def test_forecast_unavailable_below_21_observations(monkeypatch):
    monkeypatch.setattr("app.services.analysis.fetch_beta", _fake_beta)
    result = await _service([100.0] * 10).forecast("TEST", "1m")
    assert result.scenarios == []
    assert result.meta.availability == "unavailable"


@pytest.mark.asyncio
async def test_forecast_unknown_ticker_raises_404():
    with pytest.raises(BackendError) as exc_info:
        await _service([100.0] * 30).forecast("NOPE", "1m")
    assert exc_info.value.status_code == 404


def test_max_drawdown_and_liquidity_helpers():
    assert compute_max_drawdown([100.0, 110.0, 99.0, 105.0]) == pytest.approx(-0.10, abs=1e-9)
    assert compute_max_drawdown([1.0, 2.0, 3.0]) == 0.0
    assert compute_max_drawdown([5.0]) == 0.0
    assert compute_avg_dollar_volume([10.0, 20.0], [100, None]) == pytest.approx(1000.0)
    assert compute_avg_dollar_volume([10.0, 20.0], [None, None]) is None
