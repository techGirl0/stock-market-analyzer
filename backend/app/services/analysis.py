from datetime import datetime, timezone
from math import exp, log, sqrt
from app.connectors.llm import LLMConnector
from app.connectors.market import MarketDataConnector
from app.schemas.analysis import AnalysisMeta, ForecastResponse, RiskProfile
from app.schemas.v1 import Availability

DISCLAIMER = "Statistical analysis is uncertain and is not financial advice."

_HORIZON_DAYS = {
    "1y": 252,
    "3y": 756,
    "5y": 1260,
}

MU = 0.07  # assumed annual drift (lognormal model)


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
            assumptions=["At least 21 daily observations are required."],
            disclaimer=DISCLAIMER,
        )
        if len(candles) < 21:
            return RiskProfile(score=None, components={}, meta=meta)

        prices = [float(c.close) for c in candles]
        returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
        mean = sum(returns) / len(returns)
        variance = sum((v - mean) ** 2 for v in returns) / (len(returns) - 1)
        daily_vol = sqrt(variance)
        annual_vol = daily_vol * sqrt(252) * 100  # percent

        # 52-week position: where current price sits in the 52w range (0=low, 1=high)
        low_52w = min(prices)
        high_52w = max(prices)
        current = prices[-1]
        pos_52w = (current - low_52w) / (high_52w - low_52w) if high_52w > low_52w else 0.5

        # Beta vs SPY — attempt via yfinance, fall back to 1.0
        beta = await _fetch_beta(symbol)

        # News sentiment via LLM if available
        news_sentiment: float | None = None
        if self.llm is not None:
            try:
                articles = await self.market.news(symbol, limit=10)
                headlines = [a.headline for a in articles if a.headline]
                if headlines:
                    news_sentiment = await self.llm.sentiment_score(symbol, headlines)
            except Exception:
                pass

        score, components = _compute_risk_score(
            annual_vol=annual_vol,
            beta=beta,
            pos_52w=pos_52w,
            news_sentiment=news_sentiment,
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

        days = _resolve_days(horizon)
        scenarios = _compute_scenarios(current_price, annual_vol, [horizon], days_override=days)
        # Strip label key — ForecastResponse.scenarios is list[dict[str, float]]
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


def _resolve_days(horizon: str) -> int:
    if horizon in _HORIZON_DAYS:
        return _HORIZON_DAYS[horizon]
    if horizon.endswith("d"):
        try:
            return int(horizon[:-1])
        except ValueError:
            pass
    return 20


def _compute_risk_score(
    annual_vol: float,
    beta: float,
    pos_52w: float,
    news_sentiment: float | None,
) -> tuple[int, dict]:
    # Volatility component (40%): vol >50% → score 10, 0% → score 0
    vol_score = min(10.0, annual_vol / 5.0)

    # Beta component (25%): beta 0=0, 1=5, 2=10, clamp
    beta_score = min(10.0, max(0.0, (beta - 0.5) * (10.0 / 1.5)))

    # 52-week position component (20%): high position = higher risk (momentum risk)
    pos_score = pos_52w * 10.0

    # News sentiment component (15%): -1.0 (very negative) → 10, +1.0 (very positive) → 0
    if news_sentiment is not None:
        news_score = (1.0 - news_sentiment) * 5.0  # maps -1→10, +1→0
        weights = {"volatility": 0.40, "beta": 0.25, "position_52w": 0.20, "news_sentiment": 0.15}
        raw = (
            vol_score * weights["volatility"]
            + beta_score * weights["beta"]
            + pos_score * weights["position_52w"]
            + news_score * weights["news_sentiment"]
        )
        components: dict = {
            "annualized_volatility_percent": round(annual_vol, 2),
            "beta": round(beta, 3),
            "position_52w": round(pos_52w, 3),
            "news_sentiment": round(news_sentiment, 3),
        }
    else:
        # redistribute news weight across the other three
        weights = {"volatility": 0.47, "beta": 0.30, "position_52w": 0.23}
        raw = (
            vol_score * weights["volatility"]
            + beta_score * weights["beta"]
            + pos_score * weights["position_52w"]
        )
        components = {
            "annualized_volatility_percent": round(annual_vol, 2),
            "beta": round(beta, 3),
            "position_52w": round(pos_52w, 3),
        }

    score = max(1, min(10, round(raw)))
    return score, components


def _norm_ppf(p: float) -> float:
    """Rational approximation of the normal inverse CDF (Beasley-Springer-Moro)."""
    import math
    a = [0.0, -3.969683028665376e+01, 2.209460984245205e+02,
         -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [0.0, -5.447609879822406e+01, 1.615858368580409e+02,
         -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]
    c = [0.0, -7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    d = [0.0, 7.784695709041462e-03, 3.224671290700398e-01,
         2.445134137142996e+00, 3.754408661907416e+00]
    p_low, p_high = 0.02425, 1 - 0.02425
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[1]*q+c[2])*q+c[3])*q+c[4])*q+c[5])*q+c[6]) / \
               ((((d[1]*q+d[2])*q+d[3])*q+d[4])*q+1)
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[1]*r+a[2])*r+a[3])*r+a[4])*r+a[5])*r+a[6])*q / \
               (((((b[1]*r+b[2])*r+b[3])*r+b[4])*r+b[5])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[1]*q+c[2])*q+c[3])*q+c[4])*q+c[5])*q+c[6]) / \
                ((((d[1]*q+d[2])*q+d[3])*q+d[4])*q+1)


def _compute_scenarios(
    current_price: float,
    annual_vol: float,
    horizon_labels: list[str],
    days_override: int | None = None,
) -> list[dict]:
    results = []
    for label in horizon_labels:
        days = days_override if days_override is not None else _resolve_days(label)
        t = days / 252.0
        mu_t = (MU - 0.5 * annual_vol ** 2) * t
        sigma_t = annual_vol * sqrt(t)

        bear = current_price * exp(_norm_ppf(0.05) * sigma_t + mu_t)
        base = current_price * exp(_norm_ppf(0.50) * sigma_t + mu_t)
        bull = current_price * exp(_norm_ppf(0.95) * sigma_t + mu_t)

        results.append({
            "label": label,
            "bear": round(max(0.0, bear), 2),
            "base": round(base, 2),
            "bull": round(bull, 2),
        })
    return results


async def _fetch_beta(symbol: str) -> float:
    """Try to get beta from yfinance; fall back to 1.0 if unavailable."""
    try:
        import yfinance  # type: ignore
        info = yfinance.Ticker(symbol).info
        beta = info.get("beta")
        if beta is not None:
            return float(beta)
    except Exception:
        pass
    return 1.0
