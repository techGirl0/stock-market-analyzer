from uuid import uuid4


def test_register_login_and_refresh(api_client) -> None:
    email = f"backend-test-{uuid4().hex}@example.com"
    registered = api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct horse battery"},
    )
    assert registered.status_code == 201
    tokens = registered.json()
    assert tokens["access_token"]

    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct horse battery"},
    )
    assert login.status_code == 200
    refreshed = api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert refreshed.status_code == 200


def test_invalid_login_does_not_reveal_account_state(api_client) -> None:
    response = api_client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "correct horse battery"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_production_configuration_rejects_development_defaults() -> None:
    from app.core.config import Settings

    # Construct with explicit defaults, bypassing any .env file on disk.
    dev_settings = Settings(
        jwt_secret="development-only-change-me",
        market_data_provider="demo",
        _env_file=None,  # type: ignore[call-arg]
    )
    try:
        dev_settings.validate_production()
    except ValueError as exc:
        assert "JWT_SECRET" in str(exc)
    else:
        raise AssertionError("development defaults must not pass production validation")


def test_request_id_is_returned(api_client) -> None:
    response = api_client.get("/api/v1/health/live", headers={"X-Request-ID": "test-request"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request"


def test_deleted_account_token_is_rejected(api_client) -> None:
    email = f"delete-{uuid4().hex}@example.com"
    registered = api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct horse battery"},
    )
    token = registered.json()["access_token"]
    deleted = api_client.delete(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert deleted.status_code == 204
    repeated = api_client.delete(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert repeated.status_code == 401
