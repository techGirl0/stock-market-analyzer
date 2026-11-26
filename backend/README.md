# Backend

The backend is a FastAPI service under `/api/v1`. It provides health checks,
authentication, instrument search, quote/candles/news, research/chat,
watchlists, portfolios, alerts, and explicit risk/forecast availability
responses using connector interfaces and a deterministic demo connector. It
currently exposes 25 registered API routes.

Implemented routes include:

- `GET /health/live`, `GET /health/ready`
- `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`
- `DELETE /auth/me`
- `GET /instruments/search`
- `GET /instruments/{symbol}/quote`, `/candles`, `/news`, `/risk`, `/forecast`
- `POST /instruments/{symbol}/brief`, `/chat`
- `GET/POST /watchlists`, `GET/DELETE /watchlists/{id}`, `POST/DELETE /watchlists/{id}/items/{item_id}`
- `GET/POST /portfolios`, `GET /portfolios/{id}`
- `POST /portfolios/{id}/holdings`
- `GET/POST/DELETE /alerts`

All routes use typed Pydantic schemas and the shared error format. Authenticated
routes require a bearer access token. User-owned resources enforce ownership
in the service layer, and unknown resources return `404` without exposing
cross-user resource existence.

## Current backend capabilities

- Argon2id password hashing, JWT access tokens, rotating refresh tokens, logout,
  and account deletion.
- Request IDs are generated or propagated through `X-Request-ID` and returned
  on every response.
- Registration, login, and refresh requests use an in-process fixed-window
  rate limiter.
- Watchlists reject duplicate instruments.
- Portfolios calculate current holding and portfolio values through the market
  connector.
- Alerts validate symbols and support idempotent evaluation through
  `app.workers.alerts.evaluate_alerts_once`.
- Risk scores and forecast ranges calculate from validated candle returns and
  include calculation versions, assumptions, timestamps, and disclaimers.
- Research and chat use an explicit LLM connector. The default disabled
  connector is deterministic; the optional Groq connector is guarded against
  provider failures and personalized buy/sell/hold advice.

## Configuration

The service reads settings from environment variables or a local `.env` file:

| Variable | Default | Description |
|---|---|---|
| `MARKET_DATA_PROVIDER` | `demo` | `demo` or optional `yfinance` |
| `LLM_PROVIDER` | `disabled` | `disabled` or `groq` |
| `GROQ_API_KEY` | unset | Required when `LLM_PROVIDER=groq` |
| `GROQ_MODEL` | `qwen/qwen3-27b` | Groq model identifier |
| `JWT_SECRET` | development value | Must be changed outside development |
| `DATABASE_URL` | `sqlite+aiosqlite:///backend/data/app.db` | SQLAlchemy async engine target (PostgreSQL via Docker Compose) |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |

Never commit `.env` files, API keys, passwords, or production secrets.

## Database

The application uses SQLAlchemy's async engine. Local development defaults to
SQLite through `DATABASE_URL=sqlite+aiosqlite:///backend/data/app.db`; set
`DATABASE_URL` to a PostgreSQL `postgresql+asyncpg://...` URL for production.
Copy `backend/.env.example` to `.env` and provide `POSTGRES_PASSWORD` when
using PostgreSQL or Docker Compose.

Run migrations from `backend/`:

```powershell
py -m alembic upgrade head
py -m alembic downgrade base
```

The test fixture creates the SQLAlchemy schema in a temporary SQLite database.
Set `TEST_DATABASE_URL` to run the PostgreSQL integration test. Compose starts
PostgreSQL with a named volume and runs `alembic upgrade head` before the API.

## Run locally

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The OpenAPI document is available at `http://127.0.0.1:8000/docs`.

## Docker

From the repository root, run `docker compose up --build` and open
`http://127.0.0.1:8000/api/v1/health/live`. SQLite data is stored in the
named `backend-data` volume. This repository has no frontend service.

Set `MARKET_DATA_PROVIDER=yfinance` only after installing the optional
`yfinance` dependency. The default `demo` provider makes local development
and tests independent of network access.

Set `LLM_PROVIDER=groq` and `GROQ_API_KEY` to enable the Groq connector. The
default `disabled` provider is deterministic and does not make network calls.
Never commit `.env` files or provider keys.

The local SQLite store is a development persistence layer. Before deployment,
replace it with PostgreSQL/TimescaleDB and a migration runner, configure a
strong `JWT_SECRET`, and add Redis-backed caching and workers.

## Tests and worker

```powershell
py -m pytest tests -q
```

The test suite uses a temporary SQLite database and deterministic provider
responses; it does not make live network calls.

The suite covers health, market endpoints, authentication and token rotation,
watchlist ownership, portfolios, alerts, research/chat, analysis outputs,
request IDs, and production configuration checks.

Run one alert evaluation cycle manually:

```powershell
py -c "from app.workers.alerts import run_alert_evaluation; print(run_alert_evaluation())"
```

The alert worker is currently an entry point for a scheduler or queue; it is
not yet connected to a persistent background-worker service or notification
delivery channel.

## Production status

The backend is a tested development MVP. SQLite, the demo provider, the
disabled local LLM connector, and the in-process rate limiter are intended for
local development. Production still requires PostgreSQL/TimescaleDB and
migrations, Redis-backed caching and workers, a licensed market/news provider,
strong secret management, distributed rate limiting, observability, backups,
and deployment/security integration.
