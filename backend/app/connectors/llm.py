from typing import Protocol

from app.core.errors import BackendError
from app.schemas.research import ChatMessage

SYSTEM_PROMPT = (
    "You are a financial education assistant. You provide factual, evidence-based market "
    "information using only the data supplied to you. You NEVER give personalized buy, sell, "
    "or hold advice. You always remind users that statistics are uncertain and are not financial advice."
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
        return f"The backend has data for {ticker}. I cannot provide personalized buy, sell, or hold advice."

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
            f"Using ONLY the data block below, write a friendly research brief for {ticker}.\n\n"
            f"{context}\n\n"
            "Write exactly these 5 sections:\n\n"
            "## 1. Market Snapshot\n"
            "Report price, day change, market cap, P/E ratio. Explain each number in brackets. "
            "State whether data is real-time or delayed and include the fetched_at timestamp.\n\n"
            "## 2. News and Sentiment\n"
            "Summarise the headlines. State the aggregate sentiment (positive/neutral/negative). "
            "Reference headlines by [1],[2] etc. Remind the reader that news does not predict price moves.\n\n"
            "## 3. Risk Indicators\n"
            "Report the composite risk score and each component. Explain what drove the score. "
            "Use beta to describe how the stock moves relative to the market.\n\n"
            "## 4. Forecast Scenarios\n"
            "For each horizon (1 year, 3 years, 5 years) state the bear, base and bull prices with their "
            "percentage change from today. Clearly state these are illustrative statistical ranges, "
            "not predictions, and include the assumptions (7% drift, lognormal model).\n\n"
            "## 5. Limitations\n"
            "List what data is unavailable or approximate. State that all figures are statistical estimates "
            "and that this is not financial advice.\n\n"
            "End with a one-line disclaimer."
        )
        return self._complete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])

    async def chat(self, ticker: str, context: str, messages: list[ChatMessage]) -> str:
        system = f"{SYSTEM_PROMPT}\n\nUse only this market data:\n{context}"
        history = [{"role": item.role, "content": item.content} for item in messages]
        history.insert(0, {"role": "system", "content": system})
        return self._complete(history)

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
        raw = self._complete([
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
        raw = self._complete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], max_tokens=800)
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
        return self._complete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], max_tokens=300)

    async def explain_volatility(self, ticker: str, context: str) -> str:
        prompt = (
            f"Using only this volatility data for {ticker}:\n\n{context}\n\n"
            "Write 2-3 plain English sentences explaining what volatility means for this stock. "
            "Never give buy/sell/hold advice."
        )
        return self._complete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], max_tokens=300)

    async def explain_scenarios(self, ticker: str, context: str) -> str:
        prompt = (
            f"Using only this scenario data for {ticker}:\n\n{context}\n\n"
            "Write 2-3 plain English sentences explaining what these bear/base/bull scenarios mean "
            "as illustrative statistical ranges, not predictions. Never give buy/sell/hold advice."
        )
        return self._complete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], max_tokens=300)

    def _complete(self, messages: list[dict[str, str]], max_tokens: int = 1200) -> str:
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


def _parse_sentiment(raw: str) -> tuple[str, str]:
    """Parse 'GOOD: reason' or 'BAD: reason' or 'NEUTRAL: reason' from LLM output."""
    upper = raw.upper()
    for label in ("GOOD", "BAD", "NEUTRAL"):
        if upper.startswith(label):
            parts = raw.split(":", 1)
            reason = parts[1].strip() if len(parts) > 1 else raw
            return label, reason
    return "NEUTRAL", raw
