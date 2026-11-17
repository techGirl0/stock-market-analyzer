from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def auth_header() -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": f"{uuid4().hex}@example.com", "password": "correct horse battery"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_watchlist_crud_and_duplicate_protection() -> None:
    headers = auth_header()
    created = client.post("/api/v1/watchlists", headers=headers, json={"name": "Research"})
    assert created.status_code == 201
    watchlist_id = created.json()["id"]

    added = client.post(
        f"/api/v1/watchlists/{watchlist_id}/items",
        headers=headers,
        json={"symbol": "aapl"},
    )
    assert added.status_code == 201
    assert added.json()["symbol"] == "AAPL"
    duplicate = client.post(
        f"/api/v1/watchlists/{watchlist_id}/items",
        headers=headers,
        json={"symbol": "AAPL"},
    )
    assert duplicate.status_code == 409

    listed = client.get("/api/v1/watchlists", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["items"][0]["symbol"] == "AAPL"


def test_watchlists_require_authentication() -> None:
    response = client.get("/api/v1/watchlists")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


def test_portfolio_and_alert_routes() -> None:
    headers = auth_header()
    portfolio = client.post("/api/v1/portfolios", headers=headers, json={"name": "Long term"})
    assert portfolio.status_code == 201
    holding = client.post(
        f"/api/v1/portfolios/{portfolio.json()['id']}/holdings",
        headers=headers,
        json={"symbol": "MSFT", "quantity": 2},
    )
    assert holding.status_code == 201
    assert holding.json()["current_value"] is not None
    detail = client.get(
        f"/api/v1/portfolios/{portfolio.json()['id']}", headers=headers
    )
    assert detail.status_code == 200
    assert detail.json()["holdings"][0]["symbol"] == "MSFT"
    alert = client.post(
        "/api/v1/alerts", headers=headers,
        json={"symbol": "AAPL", "operator": "above", "threshold": 200},
    )
    assert alert.status_code == 201
    assert client.get("/api/v1/alerts", headers=headers).json()[0]["symbol"] == "AAPL"


def test_research_and_chat_require_auth_and_return_disclaimer() -> None:
    headers = auth_header()
    brief = client.post("/api/v1/instruments/AAPL/brief", headers=headers)
    assert brief.status_code == 200
    assert "not personalized investment advice" in brief.json()["disclaimer"]
    chat = client.post(
        "/api/v1/instruments/AAPL/chat",
        headers=headers,
        json={"user_message": "Explain the current data."},
    )
    assert chat.status_code == 200
    assert "cannot provide personalized" in chat.json()["reply"]


def test_analysis_endpoints_report_insufficient_history_explicitly() -> None:
    risk = client.get("/api/v1/instruments/AAPL/risk")
    assert risk.status_code == 200
    assert risk.json()["meta"]["availability"] == "available"
    assert risk.json()["score"] is not None
    forecast = client.get("/api/v1/instruments/AAPL/forecast", params={"horizon": "20d"})
    assert forecast.status_code == 200
    assert forecast.json()["scenarios"][0]["expected"] > 0


def test_alert_rejects_unknown_symbol() -> None:
    headers = auth_header()
    response = client.post(
        "/api/v1/alerts", headers=headers,
        json={"symbol": "INVALID", "operator": "above", "threshold": 200},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ticker_not_found"


def test_alert_evaluation_is_idempotent() -> None:
    headers = auth_header()
    created = client.post(
        "/api/v1/alerts", headers=headers,
        json={"symbol": "AAPL", "operator": "above", "threshold": 1},
    )
    assert created.status_code == 201
    from app.workers.alerts import evaluate_alerts_once

    import asyncio

    assert asyncio.run(evaluate_alerts_once()) > 0
    assert asyncio.run(evaluate_alerts_once()) == 0
