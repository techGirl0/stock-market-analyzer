from groq import Groq
from dotenv import load_dotenv
from stock_data import run_pipeline, format_pipeline_for_prompt
import os
import re

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "qwen/qwen3.8-27b"

SYSTEM_PROMPT = """You are a friendly stock market assistant for people who know nothing about finance.

Rules you must always follow:
1. Only use the data block provided. Never use your own knowledge for numbers.
2. Never tell users to buy, sell, or hold a stock. This is educational only.
3. Every financial term you use must be explained in plain English immediately after.
   Example: "P/E ratio of 28 (this means investors pay $28 for every $1 the company earns)"
4. No asterisks (*) or underscores (_) for formatting. Write numbers plainly: $145 not **$145**.
5. Only use ## for section headings and - for bullet points.
6. Short sentences. No walls of text. Friendly tone.
"""


def _call_llm(prompt: str, max_tokens: int = 1200) -> str:
    client = Groq(api_key=API_KEY)
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        extra_body={"reasoning_effort": "none"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# RESEARCH BRIEF
# ─────────────────────────────────────────────────────────────────────────────

def generate_research_brief(pipeline: dict) -> str:
    ticker = pipeline["ticker"]
    context = format_pipeline_for_prompt(pipeline)

    prompt = f"""Using ONLY the data block below, write a friendly research brief for {ticker}.

{context}

Write exactly these 5 sections:

## 🏢 1. What Does This Company Do?
2-3 sentences. Explain sector and industry in plain English.

## 📊 2. How Is the Stock Doing Right Now?
Report price, day change, market cap, P/E ratio. Explain each number in brackets.
Say where the stock sits in its 52-week range in plain words.
End with: (Source: yfinance, {pipeline['fetched_at']})

## 📰 3. What's in the News?
Summarise the headlines. Is the mood good, bad or mixed? Reference by [1],[2] etc.
Remind the reader that news does not predict what a stock will do.

## ⚠️ 4. Risk and Volatility
Report the risk score and explain what drove it.
Report the volatility forecasts for 5, 10, 20 days — explain what they mean in plain English.
Use the beta to explain how the stock moves compared to the market.

## 🔮 5. What Could Happen? (Not Predictions)
Use the scenario data to describe bear, base and bull cases for 1, 3 and 5 years.
Make it very clear these are illustrative "what if" scenarios, not predictions or advice.

End with a one-line disclaimer."""

    return _call_llm(prompt, max_tokens=1500)


# ─────────────────────────────────────────────────────────────────────────────
# NEWS SENTIMENT SCORE  (used by risk pipeline)
# ─────────────────────────────────────────────────────────────────────────────

def score_news_sentiment(ticker: str, headlines: list[dict]) -> float | None:
    """
    Sends all headlines to the LLM in one call and returns a sentiment score
    between -1.0 (all bad) and +1.0 (all good). Returns None if no headlines.
    This is called once inside run_pipeline() and cached in the pipeline dict.
    """
    if not headlines:
        return None

    titles = "\n".join(f"- {h['title']}" for h in headlines)

    prompt = f"""These are recent news headlines about {ticker} stock:

{titles}

Based only on these headlines, rate the overall news sentiment on a scale from -1.0 to +1.0:
  -1.0 = all headlines are very negative for the stock
   0.0 = neutral or mixed
  +1.0 = all headlines are very positive for the stock

Reply with a single number only. No explanation. Example: -0.3"""

    try:
        client = Groq(api_key=API_KEY)
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=10,
            extra_body={"reasoning_effort": "none"},
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content.strip()
        score = float(re.search(r"-?\d+\.?\d*", raw).group())
        return round(max(-1.0, min(1.0, score)), 2)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# NEWS FEED
# ─────────────────────────────────────────────────────────────────────────────

def get_news_feed(pipeline: dict) -> list[dict]:
    ticker = pipeline["ticker"]
    headlines = pipeline.get("news", [])
    if not headlines:
        return []

    client = Groq(api_key=API_KEY)
    results = []

    for h in headlines:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=80,
                extra_body={"reasoning_effort": "none"},
                messages=[{
                    "role": "user",
                    "content": (
                        f"News headline about {ticker} stock:\n\"{h['title']}\"\n\n"
                        f"Reply in exactly this format, one line only:\n"
                        f"SENTIMENT | plain English explanation (max 15 words)\n\n"
                        f"SENTIMENT = GOOD, BAD, or NEUTRAL. Never say buy or sell."
                    ),
                }],
            )
            raw = response.choices[0].message.content.strip()
            sentiment, explanation = _parse_sentiment(raw)
        except Exception:
            sentiment, explanation = "NEUTRAL", "Could not analyse this headline."

        results.append({
            "title": h["title"],
            "published": h["published"],
            "sentiment": sentiment,
            "explanation": explanation,
        })

    order = {"BAD": 0, "GOOD": 1, "NEUTRAL": 2}
    results.sort(key=lambda x: order.get(x["sentiment"], 2))
    return results


def _parse_sentiment(raw: str) -> tuple[str, str]:
    upper = raw.upper()
    for label in ("BAD", "GOOD", "NEUTRAL"):
        if label in upper:
            explanation = raw.split("|", 1)[1].strip() if "|" in raw else raw[upper.find(label) + len(label):].strip(" :-\n")
            explanation = re.sub(r"<[^>]+>", "", explanation).strip()
            return label, explanation or "No explanation available."
    return "NEUTRAL", "No explanation available."


# ─────────────────────────────────────────────────────────────────────────────
# RISK SCORE
# ─────────────────────────────────────────────────────────────────────────────

def get_risk_explanation(pipeline: dict) -> str:
    risk = pipeline.get("risk")
    if not risk:
        return "Not enough data to compute a risk score."

    components_text = "\n".join(
        f"- {v['label']}: {v['value']} → {v['score']}/10"
        for v in risk["components"].values()
    )

    prompt = f"""A stock tool computed this risk score for {pipeline['ticker']}:

Overall risk score: {risk['score']}/10 (1=very safe, 10=very risky)

Components:
{components_text}

Write 3-4 plain English sentences:
1. What does the overall score mean in simple terms?
2. What is driving the score the most?
3. What should someone watching this stock take away from this?

No asterisks. No markdown. Never say buy, sell, or hold. Explain every term."""

    return _call_llm(prompt, max_tokens=200)


# ─────────────────────────────────────────────────────────────────────────────
# VOLATILITY FORECAST
# ─────────────────────────────────────────────────────────────────────────────

def get_volatility_explanation(pipeline: dict) -> str:
    vol = pipeline.get("volatility")
    if not vol:
        return "Not enough data to compute volatility forecasts."

    prompt = f"""A stock tool computed these volatility forecasts for {pipeline['ticker']}:

Current 30-day volatility (annualized): {vol['current_30d']}%
Expected price movement over next 5 days:  ±{vol['forecast_5d']}%
Expected price movement over next 10 days: ±{vol['forecast_10d']}%
Expected price movement over next 20 days: ±{vol['forecast_20d']}%

Current price: {pipeline['market']['current_price']}

Write 3-4 plain English sentences explaining:
1. What volatility means (use an analogy — like a bumpy road)
2. What these specific numbers mean for this stock in dollars
3. That this is a statistical range, not a prediction

No asterisks. Explain every term. Never say buy, sell, or hold."""

    return _call_llm(prompt, max_tokens=200)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def get_scenario_explanation(pipeline: dict) -> str:
    scenarios = pipeline.get("scenarios")
    if not scenarios:
        return "Not enough data to compute scenarios."

    scenario_text = "\n".join(
        f"  {s['horizon_years']} year(s): worse case ${s['bear']} | middle ${s['base']} | better case ${s['bull']}"
        for s in scenarios
    )

    prompt = f"""A stock model computed these scenarios for {pipeline['ticker']}:

Current price: {pipeline['market']['current_price']}

{scenario_text}

These use a standard finance model (lognormal with 7% assumed annual growth and actual volatility).
They are NOT predictions — they are "what if" illustrations.

Write a friendly explanation with these parts:
1. Explain in simple terms what a "worse case / middle / better case" scenario means
2. Walk through the 1-year and 5-year numbers in plain English with dollar amounts
3. Emphasise clearly that these are not predictions and the future is uncertain

No asterisks. No markdown except headings. Never say buy, sell, or hold."""

    return _call_llm(prompt, max_tokens=300)


# ─────────────────────────────────────────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────────────────────────────────────────

def chat_with_ai(pipeline: dict, user_message: str, history: list) -> tuple[str, list]:
    client = Groq(api_key=API_KEY)
    context = format_pipeline_for_prompt(pipeline)

    system = f"""{SYSTEM_PROMPT}

Here is the current data for {pipeline['ticker']} — use this as your only source of numbers:

{context}
"""
    history.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        extra_body={"reasoning_effort": "none"},
        messages=[{"role": "system", "content": system}] + history,
    )

    reply = response.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": reply})
    return reply, history
