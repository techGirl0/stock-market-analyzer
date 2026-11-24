import asyncio
from typing import Protocol

from app.core.errors import BackendError
from app.schemas.research import ChatMessage

SYSTEM_PROMPT = (
    "You are a financial education assistant. You provide factual, evidence-based market "
    "information using only the data supplied to you. You NEVER give personalized buy, sell, "
    "or hold advice. You always remind users that statistics are uncertain and are not financial advice."
)

CHAT_CAPABILITY_PREAMBLE = (
    "You can answer questions about: current price, day change, market cap, P/E ratio, "
    "annualised volatility, beta, 52-week range, news headlines and sentiment, composite risk score, "
    "and illustrative forecast scenarios for the selected stock. "
    "You cannot answer questions about: other stocks not in the data block, macroeconomic forecasts, "
    "tax or legal advice, guaranteed price targets, or whether to buy, sell or hold. "
    "When a question asks about something not in the data block, say so clearly. "
    "When you use a figure, state which data item it comes from (e.g. 'According to the market data...'). "
    "When data is marked unavailable, say it is unavailable instead of estimating."
)


class LLMConnector(Protocol):
    async def brief(self, ticker: str, context: str) -> str: ...
    async def chat(self, ticker: str, context: str, messages: list[ChatMessage]) -> str: ...
    async def sentiment_score(self, ticker: str, headlines: list[str]) -> float | None: ...
    async def news_feed(self, ticker: str, headlines: list[str]) -> list[dict]: ...
    async def explain_risk(self, ticker: str, context: str) -> str: ...
    async def explain_volatility(self, ticker: str, context: str) -> str: ...
    async def explain_scenarios(self, ticker: str, context: str) -> str: ...


class DisabledLLMConnector:
    """Safe local implementation until an LLM provider is configured."""

    async def brief(self, ticker: str, context: str) -> str:
        return f"Research data for {ticker} is available from the backend. {context}"

    async def chat(self, ticker: str, context: str, messages: list[ChatMessage]) -> str:
        return (
            f"I can answer questions about {ticker}'s price, volatility, risk and forecast scenarios "
            "using the available market data. I cannot provide personalized buy, sell, or hold advice."
        )

    async def sentiment_score(self, ticker: str, headlines: list[str]) -> float | None:
        return None

    async def news_feed(self, ticker: str, headlines: list[str]) -> list[dict]:
        return [{"headline": h, "sentiment": "NEUTRAL", "reason": "LLM disabled"} for h in headlines]

    async def explain_risk(self, ticker: str, context: str) -> str:
        return f"Risk explanation for {ticker} requires an LLM provider."

    async def explain_volatility(self, ticker: str, context: str) -> str:
        return f"Volatility explanation for {ticker} requires an LLM provider."

    async def explain_scenarios(self, ticker: str, context: str) -> str:
        return f"Scenario explanation for {ticker} requires an LLM provider."


class GroqLLMConnector:
    def __init__(self, api_key: str, model: str) -> None:
        try:
            from groq import Groq
        except ImportError as exc:
            raise BackendError("llm_unavailable", "The Groq connector is not installed.", 503) from exc
        self._client = Groq(api_key=api_key)
        self._model = model

    async def brief(self, ticker: str, context: str) -> str:
        prompt = (
            f"Using ONLY the data block below, write a concise research brief for {ticker}.\n\n"
            f"{context}\n\n"
            "Write exactly these 5 sections. Be concise — 2-4 sentences per section maximum.\n\n"
            "## 1. Market Snapshot\n"
            "One sentence each: price, day change, market cap, P/E ratio. No explanations in brackets.\n\n"
            "## 2. News and Sentiment\n"
            "One sentence summary. List headlines as bullets with [SENTIMENT] label. "
            "One sentence: news does not predict price moves.\n\n"
            "## 3. Risk Indicators\n"
            "State the risk score and label. List each component as a bullet (name: value). "
            "One sentence explaining the main driver.\n\n"
            "## 4. Forecast Scenarios\n"
            "One sentence: these are illustrative ranges, not predictions (lognormal, 7% drift).\n"
            "Then a markdown table with columns: Horizon | Bear Case | Base Case | Bull Case\n"
            "Three rows: 1 Year, 3 Year, 5 Year. Format prices as $X.XX (Y%).\n\n"
            "## 5. Limitations\n"
            "3 bullet points: data gaps or approximations. Final line: not financial advice.\n"
        )
        return await self._acomplete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])

    async def chat(self, ticker: str, context: str, messages: list[ChatMessage]) -> str:
        system = (
            f"{SYSTEM_PROMPT}\n\n"
            f"{CHAT_CAPABILITY_PREAMBLE}\n\n"
            f"Use only this market data for {ticker}:\n{context}"
        )
        history = [{"role": item.role, "content": item.content} for item in messages]
        history.insert(0, {"role": "system", "content": system})
        return await self._acomplete(history)

    async def sentiment_score(self, ticker: str, headlines: list[str]) -> float | None:
        if not headlines:
            return None
        numbered = "\n".join(f"{i + 1}. {h}" for i, h in enumerate(headlines))
        prompt = (
            f"Rate the overall market sentiment for {ticker} based on these headlines.\n\n"
            f"{numbered}\n\n"
            "Respond with a single decimal number between -1.0 (very negative) and +1.0 (very positive). "
            "Output the number only, nothing else."
        )
        raw = await self._acomplete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], max_tokens=20)
        try:
            value = float(raw.strip())
            return max(-1.0, min(1.0, value))
        except ValueError:
            return None

    async def news_feed(self, ticker: str, headlines: list[str]) -> list[dict]:
        if not headlines:
            return []
        numbered = "\n".join(f"{i + 1}. {h}" for i, h in enumerate(headlines))
        prompt = (
            f"For each headline about {ticker}, reply with exactly one line per headline:\n"
            f"<number>. <GOOD|BAD|NEUTRAL>: <one sentence reason>\n\n"
            f"Headlines:\n{numbered}"
        )
        raw = await self._acomplete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], max_tokens=500)
        results = []
        for line in raw.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            # strip leading "1. " numbering
            if line and line[0].isdigit():
                line = line.split(".", 1)[-1].strip()
            sentiment, reason = _parse_sentiment(line)
            # match back to original headline by position
            idx = len(results)
            headline = headlines[idx] if idx < len(headlines) else line
            results.append({"headline": headline, "sentiment": sentiment, "reason": reason})
        # fill any missing entries
        for i in range(len(results), len(headlines)):
            results.append({"headline": headlines[i], "sentiment": "NEUTRAL", "reason": "No classification returned."})
        return results

    async def explain_risk(self, ticker: str, context: str) -> str:
        prompt = (
            f"Using only this risk data for {ticker}:\n\n{context}\n\n"
            "Write 2-3 plain English sentences explaining what the risk score means for a retail investor. "
            "Never give buy/sell/hold advice."
        )
        return await self._acomplete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], max_tokens=300)

    async def explain_volatility(self, ticker: str, context: str) -> str:
        prompt = (
            f"Using only this volatility data for {ticker}:\n\n{context}\n\n"
            "Write 2-3 plain English sentences explaining what volatility means for this stock. "
            "Never give buy/sell/hold advice."
        )
        return await self._acomplete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], max_tokens=300)

    async def explain_scenarios(self, ticker: str, context: str) -> str:
        prompt = (
            f"Using only this scenario data for {ticker}:\n\n{context}\n\n"
            "Write 2-3 plain English sentences explaining what these bear/base/bull scenarios mean "
            "as illustrative statistical ranges, not predictions. Never give buy/sell/hold advice."
        )
        return await self._acomplete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], max_tokens=300)

    def _complete(self, messages: list[dict[str, str]], max_tokens: int = 900) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model, messages=messages, max_tokens=max_tokens
            )
            text = response.choices[0].message.content
        except Exception as exc:
            raise BackendError("llm_unavailable", "The language model is temporarily unavailable.", 503) from exc
        if not text or any(word in text.lower() for word in ("you should buy", "you should sell", "hold this stock")):
            raise BackendError("llm_output_invalid", "The generated response failed safety validation.", 502)
        return text.strip()

    async def _acomplete(self, messages: list[dict[str, str]], max_tokens: int = 900) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._complete(messages, max_tokens))


def _parse_sentiment(raw: str) -> tuple[str, str]:
    """Parse 'GOOD: reason' or 'BAD: reason' or 'NEUTRAL: reason' from LLM output."""
    upper = raw.upper()
    for label in ("GOOD", "BAD", "NEUTRAL"):
        if upper.startswith(label):
            parts = raw.split(":", 1)
            reason = parts[1].strip() if len(parts) > 1 else raw
            return label, reason
    return "NEUTRAL", raw
