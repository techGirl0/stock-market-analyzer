"""
Pydantic schemas for AI-generated responses.

Every result carries:
  - sources        : list of DataSource describing where each figure came from
  - as_of          : UTC timestamp of the underlying data
  - assumptions    : explicit modelling assumptions (e.g. drift rate)
  - limitations    : what is unavailable or approximate
  - disclaimer     : standard not-financial-advice note

Forecasts additionally carry:
  - horizon        : structured label + trading-day count (never a single price target)
  - percentile_low / percentile_high : uncertainty bounds (5th / 95th pct by default)
  - confidence     : LOW | MEDIUM | HIGH based on data quality
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

DISCLAIMER = "Statistical estimates only. Not personalized investment advice."


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------

class DataSource(BaseModel):
    """Provenance for a single figure or data series."""

    label: str = Field(description="Human-readable name, e.g. 'yfinance daily close'")
    provider: str = Field(description="Provider identifier, e.g. 'yfinance'")
    as_of: datetime = Field(description="UTC timestamp when data was fetched")
    delayed: bool = Field(description="True if the feed is delayed rather than real-time")

    model_config = {
        "json_schema_extra": {
            "example": {
                "label": "yfinance daily close",
                "provider": "yfinance",
                "as_of": "2026-11-23T11:34:25Z",
                "delayed": True,
            }
        }
    }


Confidence = Literal["HIGH", "MEDIUM", "LOW", "UNAVAILABLE"]


# ---------------------------------------------------------------------------
# Research Brief
# ---------------------------------------------------------------------------

class BriefSource(BaseModel):
    """One cited evidence item inside a brief."""

    index: int = Field(description="Reference number used in the brief text, e.g. [1]")
    headline: str
    publisher: str | None = None
    published_at: datetime | None = None
    source_url: str | None = None


class AiBriefResponse(BaseModel):
    """Full AI-generated research brief for a single symbol."""

    ticker: str
    company_name: str
    brief_text: str = Field(description="Markdown narrative. Figures cite sources as [n].")
    sources: list[BriefSource] = Field(
        default_factory=list,
        description="Evidence items referenced in brief_text.",
    )
    as_of: datetime = Field(description="UTC timestamp of the underlying market data.")
    generated_at: datetime
    assumptions: list[str] = Field(
        default_factory=list,
        description="Modelling assumptions used (e.g. drift rate for scenarios).",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Data gaps or approximations present in this brief.",
    )
    disclaimer: str = Field(default=DISCLAIMER)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "AAPL",
                    "company_name": "Apple Inc.",
                    "brief_text": (
                        "## 1. Market Snapshot\nAAPL trades at **$342.56** (-1.90% today) [1].\n"
                        "## 2. News and Sentiment\nSentiment is neutral (score -0.2). "
                        "XLK sold $71.4M of AAPL [2].\n"
                        "## 3. Risk Indicators\nComposite risk: **6/10** (moderate).\n"
                        "## 4. Forecast Scenarios\n1-year base: $356, bear: $236, bull: $537.\n"
                        "## 5. Limitations\nP/E and market cap sourced from delayed feed."
                    ),
                    "sources": [
                        {
                            "index": 1,
                            "headline": "AAPL price",
                            "publisher": "yfinance",
                            "published_at": "2026-11-23T11:34:25Z",
                            "source_url": None,
                        },
                        {
                            "index": 2,
                            "headline": "State Street XLK sold $71.4M of AAPL",
                            "publisher": "Reuters",
                            "published_at": "2026-11-19T09:00:00Z",
                            "source_url": "https://example.com/xlk-aapl",
                        },
                    ],
                    "as_of": "2026-11-23T11:34:25Z",
                    "generated_at": "2026-11-23T11:34:30Z",
                    "assumptions": [
                        "Scenario model: lognormal with 7% annual drift",
                        "Volatility held constant at trailing 30-day figure",
                    ],
                    "limitations": [
                        "Market cap and P/E from delayed feed",
                        "News sentiment based on headlines only, not full articles",
                    ],
                    "disclaimer": DISCLAIMER,
                },
            ]
        }
    }


# ---------------------------------------------------------------------------
# Risk Indicators
# ---------------------------------------------------------------------------

class RiskComponent(BaseModel):
    """One component of the composite risk score."""

    label: str = Field(description="Human-readable name, e.g. 'Annualized volatility'")
    value: str = Field(description="Formatted value, e.g. '24.95%'")
    score: Annotated[float, Field(ge=0, le=10)]
    weight: Annotated[float, Field(ge=0, le=1)] = Field(description="Contribution weight (0–1, sums to 1)")
    confidence: Confidence = Field(default="HIGH")


class AiRiskResponse(BaseModel):
    """Composite risk profile for a symbol."""

    ticker: str
    score: Annotated[int, Field(ge=1, le=10)] | None = Field(
        description="Overall risk score 1–10, or null when insufficient data."
    )
    label: Literal["LOW", "MODERATE", "HIGH"] | None = None
    components: list[RiskComponent] = Field(default_factory=list)
    uncertainty_range: tuple[int, int] | None = Field(
        default=None,
        description="Plausible score range given data quality, e.g. [5, 7].",
    )
    sources: list[DataSource] = Field(default_factory=list)
    as_of: datetime
    generated_at: datetime
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    disclaimer: str = Field(default=DISCLAIMER)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "AAPL",
                    "score": 6,
                    "label": "MODERATE",
                    "components": [
                        {
                            "label": "Annualized volatility", "value": "24.95%",
                            "score": 5.0, "weight": 0.4, "confidence": "HIGH",
                        },
                        {
                            "label": "Beta vs market", "value": "1.089",
                            "score": 5.3, "weight": 0.25, "confidence": "HIGH",
                        },
                        {
                            "label": "52-week position", "value": "87.6%",
                            "score": 8.8, "weight": 0.2, "confidence": "HIGH",
                        },
                        {
                            "label": "News sentiment", "value": "-0.2 (Negative)",
                            "score": 6.0, "weight": 0.15, "confidence": "MEDIUM",
                        },
                    ],
                    "uncertainty_range": [5, 7],
                    "sources": [
                        {
                            "label": "yfinance daily close", "provider": "yfinance",
                            "as_of": "2026-11-23T11:34:25Z", "delayed": True,
                        }
                    ],
                    "as_of": "2026-11-23T11:34:25Z",
                    "generated_at": "2026-11-23T11:34:30Z",
                    "assumptions": ["Beta estimated from trailing 1-year daily returns vs SPY"],
                    "limitations": ["News sentiment based on headlines only"],
                    "disclaimer": DISCLAIMER,
                },
            ]
        }
    }


# ---------------------------------------------------------------------------
# Forecast / Scenario Analysis
# ---------------------------------------------------------------------------

class ForecastHorizon(BaseModel):
    label: str = Field(description="e.g. '1y', '3y', '5y'")
    trading_days: int = Field(description="Number of trading days this horizon covers")


class ScenarioEntry(BaseModel):
    """One bear/base/bull row for a horizon. Never a single price target."""

    horizon: ForecastHorizon
    percentile_5: Annotated[float, Field(ge=0)] = Field(description="5th-percentile (bear) price")
    percentile_50: Annotated[float, Field(ge=0)] = Field(description="Median (base) price")
    percentile_95: Annotated[float, Field(ge=0)] = Field(description="95th-percentile (bull) price")
    pct_change_5: float = Field(description="% change from current to percentile_5")
    pct_change_50: float = Field(description="% change from current to percentile_50")
    pct_change_95: float = Field(description="% change from current to percentile_95")


class AiForecastResponse(BaseModel):
    """Long-term scenario analysis. All prices are percentile ranges, not targets."""

    ticker: str
    current_price: float | None = None
    scenarios: list[ScenarioEntry] = Field(default_factory=list)
    confidence: Confidence = Field(
        description="Overall confidence in the scenario model given available data."
    )
    sources: list[DataSource] = Field(default_factory=list)
    as_of: datetime
    generated_at: datetime
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    disclaimer: str = Field(default=DISCLAIMER)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "AAPL",
                    "current_price": 342.56,
                    "scenarios": [
                        {
                            "horizon": {"label": "1y", "trading_days": 252},
                            "percentile_5": 236.27, "percentile_50": 356.14, "percentile_95": 536.83,
                            "pct_change_5": -31.03, "pct_change_50": 3.96, "pct_change_95": 56.71,
                        },
                        {
                            "horizon": {"label": "3y", "trading_days": 756},
                            "percentile_5": 189.11, "percentile_50": 384.94, "percentile_95": 783.56,
                            "pct_change_5": -44.80, "pct_change_50": 12.37, "pct_change_95": 128.74,
                        },
                        {
                            "horizon": {"label": "5y", "trading_days": 1260},
                            "percentile_5": 166.21, "percentile_50": 416.07, "percentile_95": 1041.52,
                            "pct_change_5": -51.48, "pct_change_50": 21.46, "pct_change_95": 204.04,
                        },
                    ],
                    "confidence": "MEDIUM",
                    "sources": [
                        {
                            "label": "yfinance daily close (1y)", "provider": "yfinance",
                            "as_of": "2026-11-23T11:34:25Z", "delayed": True,
                        }
                    ],
                    "as_of": "2026-11-23T11:34:25Z",
                    "generated_at": "2026-11-23T11:34:30Z",
                    "assumptions": [
                        "Lognormal price model",
                        "Assumed annual drift: 7% (long-run equity average)",
                        "Volatility held constant at trailing 30-day annualized figure: 24.95%",
                        "Percentile bounds: 5th (bear), 50th (base), 95th (bull)",
                    ],
                    "limitations": [
                        "Drift assumption of 7% may not reflect company-specific outlook",
                        "Volatility assumed constant — real volatility varies over time",
                        "Scenarios are illustrative ranges, not predictions",
                    ],
                    "disclaimer": DISCLAIMER,
                },
            ]
        }
    }


# ---------------------------------------------------------------------------
# News with Sentiment
# ---------------------------------------------------------------------------

class NewsItem(BaseModel):
    """One news article with AI-labelled sentiment."""

    index: int = Field(description="1-based position in the feed")
    headline: str
    publisher: str | None = None
    published_at: datetime | None = None
    source_url: str | None = None
    summary: str | None = Field(default=None, description="Short summary (no full article text)")
    sentiment: Literal["POSITIVE", "NEGATIVE", "NEUTRAL"]
    sentiment_confidence: Confidence = Field(default="MEDIUM")
    reason: str = Field(description="One-sentence AI rationale for the sentiment label")


class AiNewsResponse(BaseModel):
    """News feed with per-article AI sentiment and an aggregate score."""

    ticker: str
    items: list[NewsItem] = Field(default_factory=list)
    aggregate_sentiment_score: float | None = Field(
        default=None,
        description=(
            "Aggregate sentiment score from -1.0 (very negative) to +1.0 (very positive),"
            " or null when unavailable."
        ),
        ge=-1.0,
        le=1.0,
    )
    aggregate_sentiment_label: Literal["POSITIVE", "NEGATIVE", "NEUTRAL"] | None = None
    aggregate_confidence: Confidence = Field(default="MEDIUM")
    sources: list[DataSource] = Field(default_factory=list)
    as_of: datetime
    generated_at: datetime
    limitations: list[str] = Field(default_factory=list)
    disclaimer: str = Field(default=DISCLAIMER)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "AAPL",
                    "items": [
                        {
                            "index": 1,
                            "headline": "State Street XLK sold $71.4M of Apple",
                            "publisher": "Reuters",
                            "published_at": "2026-11-19T09:00:00Z",
                            "source_url": "https://example.com/xlk-aapl",
                            "summary": "ETF outflow from Apple position.",
                            "sentiment": "NEGATIVE",
                            "sentiment_confidence": "HIGH",
                            "reason": "Institutional selling indicates reduced conviction in the stock.",
                        },
                        {
                            "index": 2,
                            "headline": "iShares S&P 500 Value ETF highlights Apple as top holding",
                            "publisher": "Bloomberg",
                            "published_at": "2026-11-19T08:00:00Z",
                            "source_url": "https://example.com/ive-aapl",
                            "summary": "Routine ETF composition disclosure.",
                            "sentiment": "NEUTRAL",
                            "sentiment_confidence": "HIGH",
                            "reason": "Routine ETF disclosure with no directional signal.",
                        },
                    ],
                    "aggregate_sentiment_score": -0.2,
                    "aggregate_sentiment_label": "NEGATIVE",
                    "aggregate_confidence": "MEDIUM",
                    "sources": [
                        {
                            "label": "yfinance news feed", "provider": "yfinance",
                            "as_of": "2026-11-23T11:34:25Z", "delayed": True,
                        }
                    ],
                    "as_of": "2026-11-23T11:34:25Z",
                    "generated_at": "2026-11-23T11:34:30Z",
                    "limitations": ["Sentiment based on headlines only, not full article text"],
                    "disclaimer": DISCLAIMER,
                },
            ]
        }
    }
