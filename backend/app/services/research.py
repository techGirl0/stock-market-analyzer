from datetime import datetime, timezone
from math import sqrt, exp
from app.connectors.market import MarketDataConnector
from app.connectors.llm import LLMConnector
from app.core.errors import BackendError
from app.schemas.research import BriefResponse, ChatMessage, ChatResponse
from app.services.analysis import _compute_risk_score, _compute_scenarios, _fetch_beta, _resolve_days

DISCLAIMER = "General, evidence-based information only; not personalized investment advice."


class ResearchService:
    def __init__(self, market: MarketDataConnector, llm: LLMConnector) -> None:
        self.market, self.llm = market, llm

    async def brief(self, symbol: str) -> BriefResponse:
        pipeline = await self._build_pipeline(symbol)
        context = _format_pipeline_for_prompt(pipeline)
        text = await self.llm.brief(symbol.upper(), context)
        return BriefResponse(
            ticker=symbol.upper(),
            brief_text=text,
            generated_at=datetime.now(timezone.utc),
            disclaimer=DISCLAIMER,
        )

    async def chat(self, symbol: str, messages: list[ChatMessage], user_message: str) -> ChatResponse:
        pipeline = await self._build_pipeline(symbol)
        context = _format_pipeline_for_prompt(pipeline)
        updated = [*messages, ChatMessage(role="user", content=user_message)]
        reply = await self.llm.chat(symbol.upper(), context, updated)
        updated.append(ChatMessage(role="assistant", content=reply))
        return ChatResponse(
            reply=reply,
            messages=updated,
            generated_at=datetime.now(timezone.utc),
            disclaimer=DISCLAIMER,
        )

    async def _build_pipeline(self, symbol: str) -> dict:
        """Assemble the full data pipeline mirroring ai_module/stock_data.py:run_pipeline()."""
        normalized = symbol.upper()
        if not await self.market.validate(normalized):
            raise BackendError("ticker_not_found", "The requested instrument was not recognised.", 404)

        quote = await self.market.quote(normalized)
        now = datetime.now(timezone.utc)

        # --- price history ---
        candles = await self.market.candles(
            normalized,
            start=now.replace(year=now.year - 1),
            end=now,
            interval="1d",
        )
        prices = [float(c.close) for c in candles] if candles else []

        # --- volatility ---
        annual_vol: float | None = None
        daily_vol: float | None = None
        if len(prices) >= 21:
            returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
            mean_r = sum(returns) / len(returns)
            variance = sum((v - mean_r) ** 2 for v in returns) / (len(returns) - 1)
            daily_vol = sqrt(variance)
            annual_vol = daily_vol * sqrt(252)

        # --- 52w position ---
        pos_52w: float | None = None
        low_52w: float | None = None
        high_52w: float | None = None
        if prices:
            low_52w = min(prices)
            high_52w = max(prices)
            current = prices[-1]
            pos_52w = (current - low_52w) / (high_52w - low_52w) if high_52w > low_52w else 0.5

        # --- beta ---
        beta = await _fetch_beta(normalized)

        # --- news & sentiment ---
        articles = await self.market.news(normalized, limit=10)
        headlines = [a.headline for a in articles if a.headline]
        news_items: list[dict] = []
        news_sentiment: float | None = None
        if headlines:
            news_items = await self.llm.news_feed(normalized, headlines)
            news_sentiment = await self.llm.sentiment_score(normalized, headlines)

        # --- risk score ---
        risk_score: int | None = None
        risk_components: dict = {}
        if annual_vol is not None and pos_52w is not None:
            risk_score, risk_components = _compute_risk_score(
                annual_vol=annual_vol * 100,
                beta=beta,
                pos_52w=pos_52w,
                news_sentiment=news_sentiment,
            )

        # --- scenarios ---
        scenarios: list[dict] = []
        if annual_vol is not None and prices:
            scenarios = _compute_scenarios(prices[-1], annual_vol, ["1y", "3y", "5y"])

        current_price = float(quote.price) if quote.price is not None else (prices[-1] if prices else None)

        return {
            "ticker": normalized,
            "name": quote.instrument.name,
            "current_price": current_price,
            "annual_vol_pct": round(annual_vol * 100, 2) if annual_vol is not None else None,
            "daily_vol_pct": round(daily_vol * 100, 4) if daily_vol is not None else None,
            "beta": round(beta, 3),
            "low_52w": round(low_52w, 2) if low_52w is not None else None,
            "high_52w": round(high_52w, 2) if high_52w is not None else None,
            "pos_52w": round(pos_52w, 3) if pos_52w is not None else None,
            "news_sentiment": round(news_sentiment, 3) if news_sentiment is not None else None,
            "news_items": news_items,
            "risk_score": risk_score,
            "risk_components": risk_components,
            "scenarios": scenarios,
            "source": quote.meta.source,
            "fetched_at": quote.meta.fetched_at.isoformat(),
        }


def _format_pipeline_for_prompt(p: dict) -> str:
    """Build the full LLM context string from the assembled pipeline."""
    lines = [
        f"## {p['name']} ({p['ticker']})",
        f"- Current price: ${p['current_price']}" if p.get("current_price") else "- Current price: unavailable",
        f"- Data source: {p.get('source', 'unknown')}; fetched at {p.get('fetched_at', 'unknown')}",
        "",
    ]

    # Volatility
    if p.get("annual_vol_pct") is not None:
        vol_label = (
            "LOW" if p["annual_vol_pct"] < 20
            else "MODERATE" if p["annual_vol_pct"] < 40
            else "HIGH"
        )
        lines += [
            "### Volatility",
            f"- Annualized volatility: {p['annual_vol_pct']}% ({vol_label})",
            f"- Daily volatility: {p.get('daily_vol_pct', 'N/A')}%",
            "",
        ]

    # Beta
    beta = p.get("beta")
    if beta is not None:
        beta_label = "LOW" if beta < 0.8 else "MODERATE" if beta < 1.2 else "HIGH"
        lines += [
            "### Beta",
            f"- Beta vs market: {beta} ({beta_label} market sensitivity)",
            "",
        ]

    # 52-week range
    if p.get("low_52w") is not None:
        pos = p.get("pos_52w", 0.5)
        pos_label = "near 52w low" if pos < 0.3 else "near 52w high" if pos > 0.7 else "mid-range"
        lines += [
            "### 52-Week Range",
            f"- Low: ${p['low_52w']}  High: ${p['high_52w']}",
            f"- Current position: {round(pos * 100, 1)}% of range ({pos_label})",
            "",
        ]

    # News sentiment
    if p.get("news_sentiment") is not None:
        sent_val = p["news_sentiment"]
        sent_label = "POSITIVE" if sent_val > 0.1 else "NEGATIVE" if sent_val < -0.1 else "NEUTRAL"
        lines += [
            "### News Sentiment",
            f"- Aggregate sentiment score: {sent_val} ({sent_label})",
            "",
        ]
    if p.get("news_items"):
        lines.append("### Recent Headlines")
        for item in p["news_items"][:5]:
            lines.append(f"- [{item.get('sentiment', 'NEUTRAL')}] {item.get('headline', '')}")
        lines.append("")

    # Risk score
    if p.get("risk_score") is not None:
        lines += [
            "### Composite Risk Score",
            f"- Score: {p['risk_score']}/10",
        ]
        for k, v in p.get("risk_components", {}).items():
            lines.append(f"  - {k}: {v}")
        lines.append("")

    # Scenarios
    if p.get("scenarios"):
        lines.append("### Long-Term Scenarios (illustrative, lognormal model, not predictions)")
        for s in p["scenarios"]:
            lines.append(
                f"- {s.get('label', '?')}: bear ${s.get('bear')}  base ${s.get('base')}  bull ${s.get('bull')}"
            )
        lines.append("")

    lines.append("*All figures are statistical estimates. This is not financial advice.*")
    return "\n".join(lines)
