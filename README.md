# Stock Market Analyzer

An educational market-intelligence platform for retail investors and fintech
learners. Users can search for a ticker and explore market data, related news,
transparent risk indicators, and forecast scenarios with clearly stated
uncertainty.

> This project is for education and research. It does not execute trades or
> provide personalized investment advice. Forecasts describe possible
> scenarios, not guaranteed outcomes.

## Product goals

WolfStreet Signal is being developed as a research copilot for retail
investors and fintech learners. The product goal is to take a user from a
ticker to a transparent, cited view of that company without pretending to
predict the future or make the decision for them.

The long-term vision includes five capabilities:

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

## Current delivery goals

The implementation is intentionally phased so that the team can deliver a
complete user journey rather than disconnected features:

- **By December:** implement the account foundation: register, log in, and log
  out.
- **By June:** add ticker search and market data, structured research briefs,
  watchlists and alerts, portfolios, and an AI chat experience.
- **Later vision:** event-driven news, advanced forecasting and scenario
  analysis, composite risk scoring, and administration remain outside the
  current delivery period.

The first end-to-end journeys being specified are [Search for a
Stock](documentation/UCs/SearchForAStock.md) and [Manage
Watchlist](documentation/UCs/ManageWatchList.md). Search covers ticker or
company-name lookup, a stock dashboard, quote/history/news loading states, and
clear no-results or unavailable-data handling. Watchlists cover adding,
viewing, and removing stocks with confirmation and strict per-user data
isolation.

## Documentation

- [Software Requirements Specification](documentation/SoftwareRequirementsSpecification.md)
- [Use Case Diagram](documentation/Media/UseCaseDiagram.jpg)
- [Search for a Stock use case](documentation/UCs/SearchForAStock.md)
- [Manage Watchlist use case](documentation/UCs/ManageWatchList.md)

## Project journal

The team shares the project decisions and progress on the
[WolfStreet Signal blog](https://wolfstreeetsignalblog.wordpress.com/):

- [Week 1: Introduction](https://wolfstreeetsignalblog.wordpress.com/category/introduction/)
  - Product purpose, research-first guardrails, and the scenario-based
    approach.
- [Week 2: Team, technology, and project setup](https://wolfstreeetsignalblog.wordpress.com/category/week-2/)
  - Technology choices, responsibilities, GitHub workflow, and project
    management.
- [Week 3: Requirements and overall use cases](https://wolfstreeetsignalblog.wordpress.com/category/week-3/)
  - Delivery scope, SRS, use-case areas, and explicit out-of-scope decisions.
- [Week 4: Search and watchlist use cases](https://wolfstreeetsignalblog.wordpress.com/2026/10/27/week-4-search-and-watchlist-use-cases/)
  - Detailed user journeys, alternative flows, activity diagrams, and
    mockups for the first two feature areas.

## Status

The repository currently contains the requirements and design documentation
for the account, search, research, watchlist, portfolio, and AI-chat goals.
Implementation will start with the account foundation, then move through the
search-to-research journey and watchlist workflows. Forecasting, risk
analysis, and the broader intelligence platform remain planned extensions
until the current delivery scope is complete.
