def test_live_health(api_client) -> None:
    response = api_client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_returns_typed_instrument(api_client) -> None:
    response = api_client.get("/api/v1/instruments/search", params={"q": "Apple"})
    assert response.status_code == 200
    assert response.json()["items"][0]["symbol"] == "AAPL"


def test_unknown_ticker_has_stable_error_shape(api_client) -> None:
    response = api_client.get("/api/v1/instruments/INVALID/quote")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ticker_not_found"


def test_quote_normalizes_lowercase_symbol(api_client) -> None:
    response = api_client.get("/api/v1/instruments/aapl/quote")
    assert response.status_code == 200
    assert response.json()["instrument"]["symbol"] == "AAPL"


def test_invalid_candle_range_is_rejected(api_client) -> None:
    response = api_client.get(
        "/api/v1/instruments/AAPL/history",
        params={"start": "2026-01-02T00:00:00Z", "end": "2026-01-01T00:00:00Z"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_history_is_bounded_and_includes_data_metadata(api_client) -> None:
    response = api_client.get(
        "/api/v1/instruments/AAPL/history",
        params={"limit": 2, "interval": "1d"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["source"] == "DemoMarketDataConnector"
    assert body["delayed"] is True
    assert body["availability"] == "available"
    assert body["fetched_at"].endswith("+00:00") or body["fetched_at"].endswith("Z")


def test_history_rejects_invalid_interval_and_limit(api_client) -> None:
    invalid_interval = api_client.get(
        "/api/v1/instruments/AAPL/history", params={"interval": "2d"}
    )
    invalid_limit = api_client.get(
        "/api/v1/instruments/AAPL/history", params={"limit": 501}
    )
    assert invalid_interval.status_code == 422
    assert invalid_limit.status_code == 422


def test_query_validation_uses_error_contract(api_client) -> None:
    response = api_client.get("/api/v1/instruments/search")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_news_items_are_typed(api_client) -> None:
    response = api_client.get("/api/v1/instruments/AAPL/news")
    assert response.status_code == 200
    items = response.json()
    assert items, "demo provider returns one news item"
    item = items[0]
    assert item["headline"]
    assert item["sentiment"] in ("GOOD", "BAD", "NEUTRAL")
    assert "reason" in item
