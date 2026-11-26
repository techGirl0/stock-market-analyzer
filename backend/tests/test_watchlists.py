from tests.support import headers, register


def test_watchlist_crud_and_persistence(api_client):
    token = register(api_client)
    auth = headers(token)
    created = api_client.post("/api/v1/watchlists", headers=auth, json={"name": "Tech"})
    assert created.status_code == 201
    watchlist_id = created.json()["id"]

    listed = api_client.get("/api/v1/watchlists?limit=50&offset=0", headers=auth)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == watchlist_id
    assert api_client.get(f"/api/v1/watchlists/{watchlist_id}", headers=auth).status_code == 200

    added = api_client.post(
        f"/api/v1/watchlists/{watchlist_id}/items",
        headers=auth,
        json={"symbol": "aapl"},
    )
    assert added.status_code == 201
    item_id = added.json()["id"]
    duplicate = api_client.post(
        f"/api/v1/watchlists/{watchlist_id}/items",
        headers=auth,
        json={"symbol": "AAPL"},
    )
    assert duplicate.status_code == 409
    assert api_client.delete(
        f"/api/v1/watchlists/{watchlist_id}/items/{item_id}", headers=auth
    ).status_code == 204
    assert api_client.delete(f"/api/v1/watchlists/{watchlist_id}", headers=auth).status_code == 204
    assert api_client.get(f"/api/v1/watchlists/{watchlist_id}", headers=auth).status_code == 404


def test_watchlist_validation_isolation_and_authentication(api_client):
    first = register(api_client, "first@example.com")
    second = register(api_client, "second@example.com")
    created = api_client.post(
        "/api/v1/watchlists",
        headers=headers(first),
        json={"name": "Private"},
    )
    watchlist_id = created.json()["id"]
    assert api_client.get(f"/api/v1/watchlists/{watchlist_id}", headers=headers(second)).status_code == 404
    unknown = api_client.post(
        f"/api/v1/watchlists/{watchlist_id}/items",
        headers=headers(first),
        json={"symbol": "XXXX"},
    )
    assert unknown.status_code == 404
    assert unknown.json()["error"]["message"] == 'Ticker "XXXX" was not found.'
    assert api_client.get("/api/v1/watchlists").status_code == 401


def test_watchlist_has_no_update_routes(api_client):
    paths = api_client.get("/openapi.json").json()["paths"]
    assert "/api/v1/watchlists/{watchlist_id}" in paths
    assert "put" not in paths["/api/v1/watchlists/{watchlist_id}"]
    assert "patch" not in paths["/api/v1/watchlists/{watchlist_id}"]
