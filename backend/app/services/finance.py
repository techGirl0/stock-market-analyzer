from math import exp, log, sqrt

MU = 0.07  # assumed annual drift (lognormal model)

_HORIZON_DAYS = {
    "1y": 252,
    "3y": 756,
    "5y": 1260,
}

import logging
logger = logging.getLogger(__name__)


def resolve_horizon_days(horizon: str) -> int:
    if horizon in _HORIZON_DAYS:
        return _HORIZON_DAYS[horizon]
    if horizon.endswith("d"):
        try:
            return int(horizon[:-1])
        except ValueError:
            pass
    return 20


def compute_risk_score(
    annual_vol: float,
    beta: float,
    pos_52w: float,
    news_sentiment: float | None,
) -> tuple[int, dict]:
    vol_score = min(10.0, annual_vol / 5.0)
    beta_score = min(10.0, max(0.0, (beta - 0.5) * (10.0 / 1.5)))
    pos_score = pos_52w * 10.0

    if news_sentiment is not None:
        news_score = (1.0 - news_sentiment) * 5.0
        weights = {"volatility": 0.40, "beta": 0.25, "position_52w": 0.20, "news_sentiment": 0.15}
        raw = (
            vol_score * weights["volatility"]
            + beta_score * weights["beta"]
            + pos_score * weights["position_52w"]
            + news_score * weights["news_sentiment"]
        )
        components: dict = {
            "Annualized Volatility": f"{round(annual_vol, 2)}%",
            "Beta vs Market": round(beta, 3),
            "52-Week Position": f"{round(pos_52w * 100, 1)}%",
            "News Sentiment": round(news_sentiment, 2),
        }
    else:
        weights = {"volatility": 0.47, "beta": 0.30, "position_52w": 0.23}
        raw = (
            vol_score * weights["volatility"]
            + beta_score * weights["beta"]
            + pos_score * weights["position_52w"]
        )
        components = {
            "Annualized Volatility": f"{round(annual_vol, 2)}%",
            "Beta vs Market": round(beta, 3),
            "52-Week Position": f"{round(pos_52w * 100, 1)}%",
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


def compute_scenarios(
    current_price: float,
    annual_vol: float,
    horizon_labels: list[str],
    days_override: int | None = None,
) -> list[dict]:
    results = []
    for label in horizon_labels:
        days = days_override if days_override is not None else resolve_horizon_days(label)
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


async def fetch_beta(symbol: str) -> float:
    """Try to get beta from yfinance; fall back to 1.0 if unavailable."""
    try:
        import yfinance  # type: ignore
        info = yfinance.Ticker(symbol).info
        beta = info.get("beta")
        if beta is not None:
            return float(beta)
    except Exception:
        logger.warning("Beta fetch failed for %s, defaulting to 1.0", symbol)
    return 1.0
