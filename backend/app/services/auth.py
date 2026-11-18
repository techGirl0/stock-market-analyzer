from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.core.config import Settings
from app.core.db import Database
from app.core.errors import BackendError
from app.core.security import (
    create_access_token,
    new_refresh_token,
    password_hash,
    password_matches,
    token_hash,
)


class AuthService:
    def __init__(self, database: Database, settings: Settings) -> None:
        self.database = database
        self.settings = settings

    def register(self, email: str, password: str) -> tuple[str, str]:
        normalized = email.strip().lower()
        if len(password) < 8:
            raise BackendError("validation_error", "Password must contain at least 8 characters.", 422)
        user_id = uuid4()
        try:
            with self.database.connection() as connection:
                connection.execute(
                    "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    (str(user_id), normalized, password_hash(password), datetime.now(timezone.utc).isoformat()),
                )
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise BackendError("resource_conflict", "An account already exists for this email.", 409) from exc
            raise
        return self._issue(user_id)

    def login(self, email: str, password: str) -> tuple[str, str]:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT id, password_hash FROM users WHERE email = ?", (email.strip().lower(),)
            ).fetchone()
        if row is None or not password_matches(password, row["password_hash"]):
            raise BackendError("invalid_credentials", "Email or password is incorrect.", 401)
        return self._issue(UUID(row["id"]))

    def _issue(self, user_id: UUID) -> tuple[str, str]:
        access = create_access_token(user_id, self.settings.jwt_secret)
        token_id, refresh = new_refresh_token()
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        with self.database.connection() as connection:
            connection.execute(
                "INSERT INTO refresh_tokens (token_id, user_id, token_hash, expires_at) VALUES (?, ?, ?, ?)",
                (str(token_id), str(user_id), token_hash(refresh), expires.isoformat()),
            )
        return access, refresh

    def refresh(self, refresh: str) -> tuple[str, str]:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT token_id, user_id, expires_at, revoked FROM refresh_tokens WHERE token_hash = ?",
                (token_hash(refresh),),
            ).fetchone()
            if row is None or row["revoked"] or datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):
                raise BackendError("authentication_required", "Refresh token is invalid or expired.", 401)
            connection.execute("UPDATE refresh_tokens SET revoked = 1 WHERE token_id = ?", (row["token_id"],))
        return self._issue(UUID(row["user_id"]))

    def logout(self, refresh: str) -> None:
        with self.database.connection() as connection:
            connection.execute("UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = ?", (token_hash(refresh),))

    def delete_account(self, user_id: UUID) -> None:
        with self.database.connection() as connection:
            cursor = connection.execute("DELETE FROM users WHERE id = ?", (str(user_id),))
            if cursor.rowcount == 0:
                raise BackendError("resource_not_found", "Account was not found.", 404)


def get_auth_service() -> AuthService:
    from app.core.config import get_settings
    from app.dependencies import get_database

    return AuthService(get_database(), get_settings())
