## 2. Architectural Representation: MVC type

Wolf Street Signal has two code bases today. The project as a whole is moving
from the first to the second:

1. **`ai_module/`**: a Streamlit prototype of the AI features (research brief,
   risk score, volatility forecast, scenarios, AI chat).
2. **`backend/`**: the FastAPI backend we are building as the real product. Its
   first use case, *Manage Watchlist* (CRUD), runs on PostgreSQL. A Next.js
   frontend for it is planned.

### 2.1 Current state: the Streamlit prototype is *not* a clean MVC

We want to be honest here: the prototype was built for speed, not for a clean
separation of concerns.

| File | Intended MVC role | What it really does |
|------|-------------------|---------------------|
| `ai_module/app.py` | View **and** Controller (mixed) | Draws the UI with Streamlit widgets (`st.sidebar`, `st.button`, tabs, charts) **and** handles the user input in the same script: it reads the ticker, checks which feature was chosen, calls `run_pipeline()` and caches results in `st.session_state`. |
| `ai_module/stock_data.py` | Model | Fetches market data from yfinance and computes the numbers: `run_pipeline()`, `validate_ticker()`, `_compute_risk_score()`, `_compute_scenarios()`. |
| `ai_module/ai_engine.py` | Service (outside MVC) | Wraps the Groq LLM API and turns Model data into text: `generate_research_brief()`, `get_risk_explanation()`, `chat_with_ai()`, and so on. |

This happens because Streamlit re-runs the whole script from top to bottom on
every user interaction. There is no separate controller object or routing
step, so view code and control flow end up in the same file. The prototype has
a **separate Model**, but View and Controller are **merged**. That is close to
the "Model 1 / page-centric" style, not a real MVC. Most of the code is plain
functions, so a generated class diagram of `ai_module` would be almost empty.

### 2.2 Target design: Web MVC (Model 2, action-based), split between server and client

The FastAPI backend is our MVC design, and the class diagram in section 5.2 is
generated from it.

| MVC role | Where it lives | Technology | Example (Watchlist CRUD) |
|----------|----------------|------------|--------------------------|
| **Controller** | `backend/app/controllers/` | FastAPI `APIRouter` | `controllers/watchlists.py`: `POST /watchlists`, `GET /watchlists/{id}`, `POST /watchlists/{id}/items`, ... Each endpoint receives the request, gets the current user and the service through dependency injection, and delegates the work. It contains no business logic and no SQL. |
| **Model**: entities | `backend/app/models/` | SQLAlchemy 2.0 ORM on PostgreSQL (Alembic migrations) | `User`, `Watchlist`, `WatchlistItem`, `RefreshToken` |
| **Model**: business logic | `backend/app/services/` | Plain Python classes; `WatchlistService` uses **FastCRUD** | `WatchlistService` enforces ownership, normalises symbols, validates tickers and rejects duplicate symbols; `AuthService` handles registration and login |
| **Model**: external data | `backend/app/connectors/` | Adapter interface (`MarketDataConnector`) with yfinance and demo implementations | Used by `InstrumentService` to check that a ticker exists |
| **View** | `backend/app/schemas/` + Next.js frontend | Pydantic schemas = the JSON contract; Next.js/React render it | `WatchlistCreate`, `WatchlistItemCreate` (input) and `Watchlist`, `WatchlistItem` (output). The Next.js watchlist screens (SCRUM-103) will show this data. |

**Which MVC type, and why:**

- **Action-based (request-based) Web MVC, also called "Model 2".** Every HTTP
  request is sent to exactly one controller action (a router function). The
  action calls the Model and returns data that is turned into the response.
  FastAPI, like Spring MVC or Django, works in this request → action → model →
  response cycle. It is not component-based (like JSF, or Streamlit's widget
  model).
- **The View is split between server and client.** The server does not render
  HTML. Its "view" is the Pydantic response model, which serialises the Model
  to JSON and validates incoming data. The real presentation is rendered on
  the client by Next.js. This is the usual MVC variant for a REST API with a
  separate frontend.
- **The Model has two layers: services and entities.** We do not let
  controllers use the ORM directly. A service layer between them keeps the
  rules (ownership checks, ticker validation, duplicate detection) in one
  testable place, and FastCRUD gives the services the standard CRUD
  operations. FastAPI does not generate CRUD itself, so we use this library.

### 2.3 Differences between the prototype and the target design

| Aspect | Streamlit prototype (`ai_module`) | FastAPI design (`backend`) |
|--------|-----------------------------------|----------------------------|
| View / Controller | Mixed in `app.py` | Separate: routers (Controller) vs. schemas + Next.js (View) |
| Model | Functions in `stock_data.py`, no persistence | SQLAlchemy entities + services, persisted in PostgreSQL |
| AI / LLM | Called directly from the UI script through `ai_engine.py` | Planned behind an adapter (`connectors/llm.py`), called by services; integration is tracked in SCRUM-107 |
| Structure | Mostly functions | Classes, so pyreverse can produce a meaningful class diagram |
| Testability | Hard to test separately from the UI | Services and routers are tested with pytest and behave |

The prototype stays as a quick way to try out AI features. New use cases are
built in the FastAPI MVC structure, and the AI features will move there behind
the service and connector layers.
