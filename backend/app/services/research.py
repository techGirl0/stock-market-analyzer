from datetime import datetime, timezone
from uuid import UUID
from app.connectors.market import MarketDataConnector
from app.connectors.llm import LLMConnector
from app.core.errors import BackendError
from app.schemas.research import BriefResponse, ChatMessage, ChatResponse

DISCLAIMER = "General, evidence-based information only; not personalized investment advice."

class ResearchService:
    def __init__(self, market: MarketDataConnector, llm: LLMConnector) -> None:
        self.market, self.llm = market, llm

    async def brief(self, symbol: str) -> BriefResponse:
        quote = await self._quote(symbol)
        price = f"${quote.price}" if quote.price is not None else "unavailable"
        context = (
            f"## Market snapshot\n- {quote.instrument.name} ({quote.instrument.symbol})\n"
            f"- Current price: {price}\n"
            f"- Data source: {quote.meta.source}; fetched at {quote.meta.fetched_at.isoformat()}\n\n"
        )
        text = await self.llm.brief(quote.instrument.symbol, context)
        return BriefResponse(ticker=quote.instrument.symbol, brief_text=text,
                             generated_at=datetime.now(timezone.utc), disclaimer=DISCLAIMER)

    async def chat(self, symbol: str, messages: list[ChatMessage], user_message: str) -> ChatResponse:
        quote = await self._quote(symbol)
        context = f"Ticker {quote.instrument.symbol}, price {quote.price}, source {quote.meta.source}."
        updated = [*messages, ChatMessage(role="user", content=user_message)]
        reply = await self.llm.chat(quote.instrument.symbol, context, updated)
        updated.append(ChatMessage(role="assistant", content=reply))
        return ChatResponse(reply=reply, messages=updated, generated_at=datetime.now(timezone.utc), disclaimer=DISCLAIMER)

    async def _quote(self, symbol: str):
        if not await self.market.validate(symbol):
            raise BackendError("ticker_not_found", "The requested instrument was not recognised.", 404)
        return await self.market.quote(symbol)
