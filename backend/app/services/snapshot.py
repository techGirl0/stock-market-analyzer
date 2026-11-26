"""One assembled view of everything the analysis and research features need.

Every consumer that needs "the market picture for a symbol" goes through
build_snapshot so the gathering logic (quote, candles, volatility, beta, news)
exists exactly once.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.connectors.llm import LLMConnector
from app.schemas.v1 import NewsItem
from app.services.finance import compute_risk_score, position_52w, realized_volatility
from app.services.instruments import InstrumentService
from app.services.news import label_articles

logger = logging.getLogger(__name__)

MIN_OBSERVATIONS = 21


@dataclass
class MarketSnapshot:
    symbol: str
    name: str
    current_price: float | None
    day_change_pct: float | None
    market_cap: int | None
    pe_ratio: float | None
    closes: list[float] = field(default_factory=list)
    volumes: list[int | None] = field(default_factory=list)
    daily_vol: float | None = None
    annual_vol: float | None = None  # fraction, e.g. 0.35 == 35%
    low_52w: float | None = None
    high_52w: float | None = None
    pos_52w: float | None = None
    beta: float = 1.0
    news_items: list[NewsItem] = field(default_factory=list)
    news_sentiment: float | None = None
    source: str = "unknown"
    delayed: bool = True
    availability: str = "unavailable"
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    as_of: datetime | None = None

    @property
    def has_history(self) -> bool:
        return len(self.closes) >= MIN_OBSERVATIONS

    def risk(self) -> tuple[int | None, dict[str, str | float | None]]:
        """Composite risk score and its display components."""
        if self.annual_vol is None or self.pos_52w is None:
            return None, {}
        return compute_risk_score(
            annual_vol=self.annual_vol * 100,
            beta=self.beta,
            pos_52w=self.pos_52w,
            news_sentiment=self.news_sentiment,
        )


async def year_closes(
    instruments: InstrumentService, symbol: str
) -> tuple[list[float], list[int | None]]:
    """One year of daily closes and volumes — the shared analysis window."""
    now = datetime.now(timezone.utc)
    page = await instruments.candles(
        symbol, start=now.replace(year=now.year - 1), end=now, interval="1d", limit=1000
    )
    return [float(c.close) for c in page.items], [c.volume for c in page.items]


async def build_snapshot(
    instruments: InstrumentService, llm: LLMConnector, symbol: str
) -> MarketSnapshot:
    normalized = symbol.strip().upper()

    quote = await instruments.quote(normalized)
    closes, volumes = await year_closes(instruments, normalized)

    daily_vol: float | None = None
    annual_vol: float | None = None
    vol = realized_volatility(closes) if len(closes) >= MIN_OBSERVATIONS else None
    if vol is not None:
        daily_vol, annual_vol = vol

    low_52w: float | None = None
    high_52w: float | None = None
    pos_52w: float | None = None
    if closes:
        low_52w, high_52w, pos_52w = position_52w(closes)

    beta = await instruments.beta(normalized)

    news_items: list[NewsItem] = []
    news_sentiment: float | None = None
    try:
        articles = (await instruments.news(normalized, limit=10)).items
        news_items = await label_articles(llm, normalized, articles)
        headlines = [a.headline for a in articles if a.headline]
        if headlines:
            news_sentiment = await llm.sentiment_score(normalized, headlines)
    except Exception:
        logger.warning("News sentiment fetch failed for %s", normalized)

    return MarketSnapshot(
        symbol=normalized,
        name=quote.instrument.name,
        current_price=float(quote.price) if quote.price is not None else (closes[-1] if closes else None),
        day_change_pct=float(quote.change_percent) if quote.change_percent is not None else None,
        market_cap=quote.market_cap,
        pe_ratio=round(float(quote.pe_ratio), 2) if quote.pe_ratio is not None else None,
        closes=closes,
        volumes=volumes,
        daily_vol=daily_vol,
        annual_vol=annual_vol,
        low_52w=low_52w,
        high_52w=high_52w,
        pos_52w=pos_52w,
        beta=beta,
        news_items=news_items,
        news_sentiment=news_sentiment,
        source=quote.meta.source,
        delayed=quote.meta.delayed,
        availability=quote.meta.availability,
        fetched_at=quote.meta.fetched_at,
        as_of=quote.as_of,
    )
