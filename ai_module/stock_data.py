import yfinance as yf
import pandas as pd
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(ticker: str) -> dict:
    """
    Single entry point. Fetches all data and computes all numbers for a ticker.
    Returns one dict that every feature reads from.
    The LLM never computes numbers — it only narrates what's in this dict.
    """
    stock = yf.Ticker(ticker)
    info = stock.info
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    result = {
        "ticker": ticker.upper(),
        "fetched_at": fetched_at,
        "ok": True,
        "error": None,
    }

    # ── Company info ──────────────────────────────────────────────────────────
    result["company"] = {
        "name": info.get("longName", "N/A"),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "description": info.get("longBusinessSummary", "No description available."),
    }

    # ── Market snapshot ───────────────────────────────────────────────────────
    current = info.get("currentPrice") or info.get("regularMarketPrice")
    prev = info.get("previousClose")
    day_change = f"{((current - prev) / prev * 100):+.2f}%" if current and prev else "N/A"

    result["market"] = {
        "current_price": current,
        "previous_close": prev,
        "day_change_pct": day_change,
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "avg_volume": info.get("averageVolume"),
    }

    # ── Price history calculations ────────────────────────────────────────────
    try:
        hist = stock.history(period="1y")
        spy_hist = yf.Ticker("SPY").history(period="1y")

        if len(hist) > 21:
            returns = hist["Close"].pct_change().dropna()

            # Volatility: annualized std of last 30 trading days
            vol_30d = round(returns.tail(21).std() * (252 ** 0.5) * 100, 2)

            # Volatility forecast: next 5/10/20 days using last 30d vol
            daily_vol = returns.tail(21).std()
            result["volatility"] = {
                "current_30d": vol_30d,
                "forecast_5d": round(daily_vol * (5 ** 0.5) * 100, 2),
                "forecast_10d": round(daily_vol * (10 ** 0.5) * 100, 2),
                "forecast_20d": round(daily_vol * (20 ** 0.5) * 100, 2),
            }

            # Beta vs SPY
            if len(spy_hist) > 21:
                spy_returns = spy_hist["Close"].pct_change().dropna()
                aligned = pd.concat([returns, spy_returns], axis=1).dropna()
                aligned.columns = ["stock", "spy"]
                cov = aligned["stock"].cov(aligned["spy"])
                var = aligned["spy"].var()
                beta = round(cov / var, 2) if var != 0 else None
            else:
                beta = None

            result["risk_inputs"] = {
                "volatility_30d": vol_30d,
                "beta": beta,
                "52w_position_pct": _52w_position(current, info),
            }

            # Long-term scenarios: 1, 3, 5 year using lognormal model
            result["scenarios"] = _compute_scenarios(
                current_price=current,
                annual_vol=vol_30d / 100,
                horizons=[1, 3, 5],
            )
        else:
            result["volatility"] = None
            result["risk_inputs"] = None
            result["scenarios"] = None

    except Exception as e:
        result["volatility"] = None
        result["risk_inputs"] = None
        result["scenarios"] = None

    # ── Risk score ────────────────────────────────────────────────────────────
    if result["risk_inputs"]:
        result["risk"] = _compute_risk_score(result["risk_inputs"])
    else:
        result["risk"] = None

    # ── News headlines ────────────────────────────────────────────────────────
    try:
        raw_news = stock.news or []
        headlines = []
        for item in raw_news[:8]:
            content = item.get("content", {})
            if isinstance(content, dict):
                title = content.get("title", "")
                pub = content.get("pubDate", "") or content.get("displayTime", "")
            else:
                title = item.get("title", "")
                pub = item.get("providerPublishTime", "")
            if title:
                headlines.append({"title": title, "published": str(pub)})
        result["news"] = headlines
    except Exception:
        result["news"] = []

    return result


# ─────────────────────────────────────────────────────────────────────────────
# HELPER CALCULATIONS
# ─────────────────────────────────────────────────────────────────────────────

def _52w_position(price, info) -> float | None:
    low = info.get("fiftyTwoWeekLow")
    high = info.get("fiftyTwoWeekHigh")
    if price and low and high and high != low:
        return round((price - low) / (high - low) * 100, 1)
    return None


def _compute_risk_score(inputs: dict) -> dict:
    """Turns volatility, beta, 52w position into a 1-10 score with breakdown."""
    scores = []
    components = {}

    vol = inputs.get("volatility_30d")
    if isinstance(vol, (int, float)):
        if vol < 15:   v = 2
        elif vol < 25: v = 4
        elif vol < 35: v = 6
        elif vol < 50: v = 8
        else:          v = 10
        components["volatility"] = {"label": "Price swings (volatility)", "value": f"{vol}%", "score": v}
        scores.append((v, 0.5))

    beta = inputs.get("beta")
    if isinstance(beta, (int, float)):
        ab = abs(beta)
        if ab < 0.5:   b = 2
        elif ab < 0.8: b = 3
        elif ab < 1.2: b = 5
        elif ab < 1.6: b = 7
        else:          b = 9
        components["beta"] = {"label": "Sensitivity to market (beta)", "value": str(beta), "score": b}
        scores.append((b, 0.3))

    pos = inputs.get("52w_position_pct")
    if isinstance(pos, (int, float)):
        if pos > 90:   p = 8
        elif pos > 70: p = 6
        elif pos > 40: p = 4
        elif pos > 20: p = 3
        else:          p = 5
        components["52w_position"] = {"label": "Position in yearly range", "value": f"{pos}%", "score": p}
        scores.append((p, 0.2))

    if not scores:
        return None

    total_w = sum(w for _, w in scores)
    weighted = sum(s * w for s, w in scores) / total_w
    final = max(1, min(10, round(weighted)))

    return {"score": final, "components": components}


def _compute_scenarios(current_price: float, annual_vol: float, horizons: list) -> list:
    """
    Lognormal scenario model: bear/base/bull for each horizon.
    Uses assumed drift of 7% (long-run equity average) and actual volatility.
    """
    import math
    MU = 0.07  # assumed annual drift (market average)
    scenarios = []

    for T in horizons:
        drift = (MU - 0.5 * annual_vol ** 2) * T
        spread = annual_vol * (T ** 0.5)

        bear   = round(current_price * math.exp(drift - 1.645 * spread), 2)  # 5th pct
        base   = round(current_price * math.exp(drift), 2)                   # median
        bull   = round(current_price * math.exp(drift + 1.645 * spread), 2)  # 95th pct

        scenarios.append({
            "horizon_years": T,
            "bear": bear,
            "base": base,
            "bull": bull,
            "current": current_price,
        })

    return scenarios


def format_pipeline_for_prompt(data: dict) -> str:
    """
    Converts the pipeline output into a clean text block for the LLM.
    This is the single source of truth the LLM reads — it never uses its own knowledge for numbers.
    """
    m = data["market"]
    c = data["company"]
    lines = [
        f"=== DATA FOR {data['ticker']} (source: yfinance, fetched: {data['fetched_at']}) ===",
        f"Company: {c['name']} | Sector: {c['sector']} | Industry: {c['industry']}",
        "",
        "--- Market Snapshot ---",
        f"Price: {m['current_price']} | Day change: {m['day_change_pct']} | Prev close: {m['previous_close']}",
        f"Market cap: {m['market_cap']} | P/E ratio: {m['pe_ratio']}",
        f"52-week high: {m['52w_high']} | 52-week low: {m['52w_low']}",
    ]

    if data.get("risk_inputs"):
        ri = data["risk_inputs"]
        lines += [
            "",
            "--- Risk Inputs (calculated from 1 year of daily price data) ---",
            f"30-day annualized volatility: {ri['volatility_30d']}%",
            f"Beta vs SPY: {ri['beta']}",
            f"52-week position: {ri['52w_position_pct']}% (0=at yearly low, 100=at yearly high)",
        ]

    if data.get("risk") and data["risk"]:
        r = data["risk"]
        lines += [
            "",
            f"--- Composite Risk Score: {r['score']}/10 ---",
        ]
        for comp in r["components"].values():
            lines.append(f"  {comp['label']}: {comp['value']} → {comp['score']}/10")

    if data.get("volatility"):
        v = data["volatility"]
        lines += [
            "",
            "--- Volatility Forecasts (based on current 30d vol, assumes vol stays constant) ---",
            f"Expected price range over next 5 days:  ±{v['forecast_5d']}%",
            f"Expected price range over next 10 days: ±{v['forecast_10d']}%",
            f"Expected price range over next 20 days: ±{v['forecast_20d']}%",
        ]

    if data.get("scenarios"):
        lines += ["", "--- Long-Term Scenarios (lognormal model, 7% assumed drift, NOT predictions) ---"]
        for s in data["scenarios"]:
            lines.append(
                f"  {s['horizon_years']} year(s): bear ${s['bear']} | base ${s['base']} | bull ${s['bull']}"
            )

    if data.get("news"):
        lines += ["", "--- Recent News Headlines (source: yfinance) ---"]
        for i, h in enumerate(data["news"]):
            lines.append(f"  [{i+1}] {h['title']}")

    lines += ["", f"Company description: {c['description'][:500]}..."]

    return "\n".join(lines)
