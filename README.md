# Stock Market Analyzer

An educational market-intelligence platform for retail investors and fintech
learners. Users can search for a ticker and explore market data, related news,
transparent risk indicators, and forecast scenarios with clearly stated
uncertainty.

> This project is for education and research. It does not execute trades or
> provide personalized investment advice. Forecasts describe possible
> scenarios, not guaranteed outcomes.

## Vision

The platform is designed as a research copilot built around five capabilities:

- **Live market data:** Streaming candles, watchlists, and technical indicators.
- **News intelligence:** Deduplicated, ticker-linked, sentiment-scored, and
  impact-ranked news.
- **Research assistant:** Structured, cited briefs with follow-up questions.
- **Forecasting:** Probabilistic short- and long-term scenarios with a visible
  track record.
- **Risk analysis:** Decomposable stock and portfolio risk profiles.

The first six months deliberately exclude real-money trading, personalized
buy/sell recommendations, options and crypto order books, and deep-learning
forecasters as a headline feature.

## Planned architecture

The planned stack uses **FastAPI and Python** for the API, workers, data
ingestion, NLP, analytics, and machine learning, with **Next.js, React, and
TypeScript** for the frontend.

```text
Market/news providers -> ingestion -> Redis Streams
                              |
                              v
       news NLP | indicators | risk | forecasts | research agent
                              |
                              v
        PostgreSQL/TimescaleDB/pgvector + Redis cache
                              |
                              v
                    FastAPI REST/WebSocket
                              |
                              v
                         Next.js frontend
```

Core supporting technologies include PostgreSQL with TimescaleDB and pgvector,
Redis, pandas, NumPy, scikit-learn, FinBERT, spaCy, sentence-transformers,
MLflow, and standard observability tooling. Provider and model adapters keep
external services replaceable.

## Engineering principles

1. Numbers come from code; the language model explains them but never computes
   or invents them.
2. Every forecast includes a range, horizon, assumptions, and track record.
3. Use adapters at provider, model, and integration boundaries.
4. Store and exchange timestamps in UTC with versioned schemas and models.
5. Measure before introducing infrastructure such as Kafka or Kubernetes.
6. Review model claims independently before release.

User-facing language should describe insights, scenarios, risk, and historical
context. The application should avoid guarantees, target prices, and
instructional buy/sell language.

## Documentation

- [Software Requirements Specification](documentation/SoftwareRequirementsSpecification.md)
- [Use Case Diagram](documentation/UseCaseDiagram.png)

## Status

The repository currently contains the project requirements and design
documentation. Implementation will follow the staged roadmap: establish the
data and API foundations, build market and news intelligence, add risk and
forecast services, and then integrate the research assistant and frontend.
