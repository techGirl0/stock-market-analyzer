# AI Module — Stock Market Analyzer

Standalone AI feature module for the Stock Market Analyzer platform.
Built with Python + Streamlit. Runs independently — no database, Redis, Docker, or backend required.

---

## Features

| Feature | What it does |
|---|---|
| Research Brief | Generates a full plain-English summary of a stock (company, price, news, risk, scenarios). Downloadable as a styled PDF. |
| News Feed | Fetches latest headlines and labels each one GOOD / BAD / NEUTRAL using AI |
| Risk Score | Calculates a 1–10 composite risk score from volatility, beta, and 52-week position |
| Volatility Forecast | Shows expected price movement range for next 5, 10, and 20 days |
| Scenario Analysis | Projects worse / middle / better case prices for 1, 3, and 5 years |
| Chat with AI | Free-text chat about any stock; AI uses only real fetched data, never its own knowledge |
| Compare Stocks | Toggle to compare any two stocks side by side across all features |

---

## Quickstart

### 1. Install dependencies

```bash
cd ai_module
pip install -r requirements.txt
```

### 2. Set up your API key

Create a file called `.env` inside the `ai_module/` folder:

```
GROQ_API_KEY=your_key_here
```

Get a free key at [https://console.groq.com](https://console.groq.com) — no credit card needed.

> The `.env` file is gitignored and will never be committed.

### 3. Run the app

```bash
cd ai_module
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Project structure

```
ai_module/
├── app.py              # Streamlit UI — all 6 feature tabs + comparison toggle
├── ai_engine.py        # All LLM calls (Groq API) — never fetches data directly
├── stock_data.py       # Data pipeline — fetches from yfinance, computes all numbers
├── requirements.txt    # Pinned dependencies
└── .env                # Your API key (not committed)
```

### Key design rule

**The LLM never computes numbers.** `stock_data.py` fetches and calculates everything (prices, volatility, beta, risk score, scenarios). `ai_engine.py` receives a pre-formatted text block and only writes plain-English explanations. This prevents hallucinated numbers.

---

## How the pipeline works

```
User enters ticker
        ↓
run_pipeline(ticker)          ← stock_data.py, called once per ticker
        ↓
pipeline dict cached in       ← st.session_state, no repeated API calls
session_state
        ↓
Feature tab reads pipeline    ← displays numbers directly
        ↓
User clicks "Explain" / "Generate Brief" / sends chat message
        ↓
ai_engine.py formats pipeline → sends to Groq → returns plain-English text
```

---

## Connecting to the team backend

When the backend (FastAPI + database) is ready, swap `run_pipeline()` in `app.py` with an API call to the backend endpoint. Everything else stays the same — `ai_engine.py` only cares about receiving a dict with the right shape.

The expected dict keys are:

```python
{
    "ticker": str,
    "fetched_at": str,          # "YYYY-MM-DD HH:MM UTC"
    "company": {"name", "sector", "industry", "description"},
    "market": {"current_price", "previous_close", "day_change_pct",
               "market_cap", "pe_ratio", "52w_high", "52w_low", "avg_volume"},
    "volatility": {"current_30d", "forecast_5d", "forecast_10d", "forecast_20d"},  # or None
    "risk_inputs": {"volatility_30d", "beta", "52w_position_pct"},                 # or None
    "risk": {"score": int, "components": {...}},                                    # or None
    "scenarios": [{"horizon_years", "bear", "base", "bull", "current"}, ...],      # or None
    "news": [{"title": str, "published": str}, ...],
}
```

---

## Running BDD tests

From the repo root:

```bash
python3 -m behave features/
```

Expected output: **9 feature files, 28 scenarios, all passing.**

Tests cover: manage watchlist, search stock, generate research brief, manage portfolio,
chat with AI bot, view risk score, view volatility forecast, run scenario analysis,
compare stocks.

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Free API key from console.groq.com |

---

## Model

Currently using `qwen/qwen3.8-27b` via Groq with `reasoning_effort: "none"` for fast responses.
To change the model, update `MODEL` in `ai_engine.py`.
