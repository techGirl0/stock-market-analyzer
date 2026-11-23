from datetime import datetime, timezone
from app.connectors.llm import LLMConnector
from app.connectors.market import MarketDataConnector
from app.core.errors import BackendError
from app.schemas.v1 import NewsArticle


class NewsService:
    def __init__(self, market: MarketDataConnector, llm: LLMConnector) -> None:
        self.market = market
        self.llm = llm

    async def get_news(self, symbol: str, limit: int = 10) -> list[dict]:
        if not await self.market.validate(symbol):
            raise BackendError("ticker_not_found", "The requested instrument was not recognised.", 404)

        articles: list[NewsArticle] = await self.market.news(symbol, limit=limit)
        headlines = [a.headline for a in articles if a.headline]

        if not headlines:
            return []

        labelled = await self.llm.news_feed(symbol.upper(), headlines)

        # Merge sentiment labels back onto the article objects
        result = []
        for i, article in enumerate(articles):
            label_data = labelled[i] if i < len(labelled) else {"sentiment": "NEUTRAL", "reason": ""}
            result.append({
                "id": str(article.id),
                "headline": article.headline,
                "publisher": article.publisher,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "source_url": str(article.source_url) if article.source_url else None,
                "summary": article.summary,
                "sentiment": label_data.get("sentiment", "NEUTRAL"),
                "reason": label_data.get("reason", ""),
            })
        return result
