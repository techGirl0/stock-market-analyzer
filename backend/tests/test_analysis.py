"""
SCRUM-70: deterministic unit tests for AnalysisService with a fixed price
series and a fake provider. No network calls; no API key required.
"""

import pytest

from app.core.errors import BackendError
from app.services.analysis import AnalysisService
from app.services.finance import compute_avg_dollar_volume, compute_max_drawdown
from app.services.instruments import InstrumentService
from tests.fakes import FakeLLM, FixedSeriesConnector


def _service(closes: list[float], volumes: list[int] | None = None, beta: float = 1.25) -> AnalysisService:
    return AnalysisService(
        InstrumentService(FixedSeriesConnector(closes, volumes, beta=beta)),
        FakeLLM(sentiment=0.8),
    )


@pytest.mark.asyncio
async def test_risk_known_values():
    # 30 rising closes with one dip: peak 110 -> trough 99 = -10% drawdown.
    closes = [100.0 + (i % 3) * 5.0 for i in range(30)]
    closes[10] = 110.0
    closes[11] = 99.0
    service = _service(closes, volumes=[1_000] * 30)

    result = await service.risk("TEST")

    assert result.meta.availability == "available"
    assert result.score is not None and 1 <= result.score <= 10
    assert result.components["Maximum Drawdown"] == "-10.0%"
    # mean close = (3150 + 5 - 11) / 30 = 104.8 -> avg dollar volume $104,800
    assert result.components["Liquidity (Avg Daily $ Volume)"] == "$104,800"
    assert result.components["Beta vs Market"] == 1.25
    assert result.components["News Sentiment"] == 0.8
    # window and benchmark documented in the response
    assert any("Window" in a for a in result.meta.assumptions)
    assert any("Beta benchmark" in a for a in result.meta.assumptions)


@pytest.mark.asyncio
async def test_risk_unavailable_below_21_observations():
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
async def test_forecast_deterministic():
    service = _service([100.0 + (i % 5) for i in range(60)])
    first = await service.forecast("TEST", "1m")
    second = await service.forecast("TEST", "1m")
    # calculated_at is a wall-clock timestamp; the numbers must be identical
    assert first.scenarios == second.scenarios, "same input must produce identical output"
    assert first.horizon == second.horizon


@pytest.mark.asyncio
async def test_forecast_short_horizons():
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
async def test_forecast_unavailable_below_21_observations():
    result = await _service([100.0] * 10).forecast("TEST", "1m")
    assert result.scenarios == []
    assert result.meta.availability == "unavailable"


@pytest.mark.asyncio
async def test_forecast_with_two_closes_returns_unavailable_not_error():
    # Regression: exactly two closes once hit a ZeroDivisionError in the
    # sample-variance computation before the 21-observation guard.
    result = await _service([100.0, 101.0]).forecast("TEST", "1m")
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
