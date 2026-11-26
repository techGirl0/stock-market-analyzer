from app.connectors.llm import LLMConnector
from app.schemas.v1 import NewsArticle, NewsItem
from app.services.instruments import InstrumentService


async def label_articles(
    llm: LLMConnector, symbol: str, articles: list[NewsArticle]
) -> list[NewsItem]:
    """Classify articles with the LLM and merge the labels back by position.

    Headlines come from the articles themselves; the LLM's classification
    list is positional (its own padding guarantees one entry per headline).
    """
    headlines = [a.headline for a in articles if a.headline]
    if not headlines:
        return []
    labelled = await llm.news_feed(symbol.upper(), headlines)
    return [
        NewsItem(
            id=article.id,
            headline=article.headline,
            publisher=article.publisher,
            published_at=article.published_at,
            source_url=article.source_url,
            summary=article.summary,
            sentiment=label.get("sentiment") or "NEUTRAL",
            reason=str(label.get("reason") or ""),
        )
        for article, label in (
            (a, labelled[i] if i < len(labelled) else {}) for i, a in enumerate(articles)
        )
    ]


class NewsService:
    def __init__(self, instruments: InstrumentService, llm: LLMConnector) -> None:
        self.instruments = instruments
        self.llm = llm

    async def get_news(self, symbol: str, limit: int = 10) -> list[NewsItem]:
        articles = (await self.instruments.news(symbol, limit=limit)).items
        return await label_articles(self.llm, symbol, articles)
