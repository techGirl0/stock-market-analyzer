import re

_ADVICE_REQUEST_PATTERNS = (
    "should i buy",
    "should i sell",
    "should i invest",
    "should i hold",
    "is it a good time to buy",
    "is it worth buying",
    "what should i do",
    "would you recommend",
    "do you recommend",
    "tell me to buy",
    "tell me to sell",
)

ADVICE_REFUSAL = (
    "This platform does not give personalised buy, sell or hold advice. "
    "What it can help with: reviewing the composite risk score, understanding "
    "the bear/base/bull forecast scenarios, checking volatility and beta relative "
    "to the market, and reading the news sentiment summary. "
    "These are inputs you can weigh — the decision is yours."
)

_BLOCKED_PHRASES = (
    "you should buy",
    "you should sell",
    "you should hold",
    "i recommend buy",
    "i recommend sell",
    "i would buy",
    "i would sell",
    "consider buying",
    "consider selling",
    "is a buy",
    "is a sell",
    "price target of",
    "price target is",
    "guaranteed",
    "will definitely",
    "will certainly",
    "will reach $",
)

_FILTER_REPLACEMENT = (
    "This platform provides factual data only and does not give buy, sell or hold recommendations."
)


def is_advice_request(text: str) -> bool:
    lower = text.lower()
    return any(pattern in lower for pattern in _ADVICE_REQUEST_PATTERNS)


def sanitise_user_input(text: str) -> str:
    text = re.sub(r"https?://\S+", "[link removed]", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    return text.strip()


def sanitise_llm_output(text: str) -> str:
    """Strip bare URLs and HTML tags from LLM output."""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def filter_llm_output(text: str) -> str:
    """Replace any sentence containing a blocked advice phrase with a neutral substitute."""
    lower = text.lower()
    if not any(phrase in lower for phrase in _BLOCKED_PHRASES):
        return text
    result_lines: list[str] = []
    for line in text.splitlines():
        parts = re.split(r"(?<=\.)\s+", line)
        cleaned_parts: list[str] = []
        replaced = False
        for part in parts:
            if any(phrase in part.lower() for phrase in _BLOCKED_PHRASES):
                if not replaced:
                    cleaned_parts.append(_FILTER_REPLACEMENT)
                    replaced = True
            else:
                cleaned_parts.append(part)
        result_lines.append(" ".join(cleaned_parts))
    return "\n".join(result_lines)
