from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_live_health() -> None:
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_returns_typed_instrument() -> None:
    response = client.get("/api/v1/instruments/search", params={"q": "Apple"})
    assert response.status_code == 200
    assert response.json()["items"][0]["symbol"] == "AAPL"


def test_unknown_ticker_has_stable_error_shape() -> None:
    response = client.get("/api/v1/instruments/INVALID/quote")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ticker_not_found"


def test_quote_normalizes_lowercase_symbol() -> None:
    response = client.get("/api/v1/instruments/aapl/quote")
    assert response.status_code == 200
    assert response.json()["instrument"]["symbol"] == "AAPL"


def test_invalid_candle_range_is_rejected() -> None:
    response = client.get(
        "/api/v1/instruments/AAPL/candles",
        params={"start": "2026-01-02T00:00:00Z", "end": "2026-01-01T00:00:00Z"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_history_is_bounded_and_includes_data_metadata() -> None:
    response = client.get(
        "/api/v1/instruments/AAPL/candles",
        params={"limit": 2, "interval": "1d"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["meta"]["source"] == "DemoMarketDataConnector"
    assert body["meta"]["delayed"] is True
    assert body["meta"]["availability"] == "available"
    assert body["meta"]["fetched_at"].endswith("+00:00") or body["meta"]["fetched_at"].endswith("Z")

    history = client.get(
        "/api/v1/instruments/AAPL/history", params={"limit": 2, "interval": "1d"}
    )
    assert history.status_code == 200
    assert history.json()["source"] == "DemoMarketDataConnector"


def test_history_rejects_invalid_interval_and_limit() -> None:
    invalid_interval = client.get(
        "/api/v1/instruments/AAPL/candles", params={"interval": "2d"}
    )
    invalid_limit = client.get(
        "/api/v1/instruments/AAPL/candles", params={"limit": 501}
    )
    assert invalid_interval.status_code == 422
    assert invalid_limit.status_code == 422


def test_news_endpoint_returns_bounded_items() -> None:
    response = client.get(
        "/api/v1/instruments/AAPL/news", params={"limit": 1}
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_query_validation_uses_error_contract() -> None:
    response = client.get("/api/v1/instruments/search")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
