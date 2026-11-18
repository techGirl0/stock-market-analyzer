from typing import Protocol

from app.core.errors import BackendError
from app.schemas.research import ChatMessage


class LLMConnector(Protocol):
    async def brief(self, ticker: str, context: str) -> str: ...
    async def chat(self, ticker: str, context: str, messages: list[ChatMessage]) -> str: ...


class DisabledLLMConnector:
    """Safe local implementation until an LLM provider is configured."""

    async def brief(self, ticker: str, context: str) -> str:
        return f"Research data for {ticker} is available from the backend. {context}"

    async def chat(self, ticker: str, context: str, messages: list[ChatMessage]) -> str:
        return f"The backend has data for {ticker}. I cannot provide personalized buy, sell, or hold advice."


class GroqLLMConnector:
    def __init__(self, api_key: str, model: str) -> None:
        try:
            from groq import Groq
        except ImportError as exc:
            raise BackendError("llm_unavailable", "The Groq connector is not installed.", 503) from exc
        self._client = Groq(api_key=api_key)
        self._model = model

    async def brief(self, ticker: str, context: str) -> str:
        return self._complete(
            ticker,
            [{"role": "user", "content": f"Write a cited educational brief using only this data:\n{context}"}],
        )

    async def chat(self, ticker: str, context: str, messages: list[ChatMessage]) -> str:
        prompt = [{"role": item.role, "content": item.content} for item in messages]
        prompt.insert(0, {"role": "system", "content": f"Use only this data: {context}. Never give buy, sell, or hold advice."})
        return self._complete(ticker, prompt)

    def _complete(self, ticker: str, messages: list[dict[str, str]]) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model, messages=messages, max_tokens=1200
            )
            text = response.choices[0].message.content
        except Exception as exc:
            raise BackendError("llm_unavailable", "The language model is temporarily unavailable.", 503) from exc
        if not text or any(word in text.lower() for word in ("you should buy", "you should sell", "hold this stock")):
            raise BackendError("llm_output_invalid", "The generated response failed safety validation.", 502)
        return text.strip()
