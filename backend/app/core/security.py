from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.errors import BackendError

PASSWORDS = PasswordHasher()
JWT_ALGORITHM = "HS256"


def password_hash(password: str) -> str:
    return PASSWORDS.hash(password)


def password_matches(password: str, hashed: str) -> bool:
    try:
        return PASSWORDS.verify(hashed, password)
    except VerifyMismatchError:
        return False


def token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: UUID, secret: str, minutes: int = 15) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode(
        {"sub": str(user_id), "type": "access", "exp": expires},
        secret,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str, secret: str) -> UUID:
    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise ValueError
        return UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise BackendError("authentication_required", "Authentication is required.", 401) from exc


def new_refresh_token() -> tuple[UUID, str]:
    return uuid4(), uuid4().hex + uuid4().hex
