from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import BackendError
from app.core.security import (
    create_access_token,
    new_refresh_token,
    password_hash,
    password_matches,
    token_hash,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def register(self, email: str, password: str) -> tuple[str, str]:
        normalized = email.strip().lower()
        if len(password) < 8:
            raise BackendError("validation_error", "Password must contain at least 8 characters.", 422)
        user_id = uuid4()
        self.session.add(
            User(
                id=user_id,
                email=normalized,
                password_hash=password_hash(password),
                created_at=datetime.now(timezone.utc),
            )
        )
        try:
            await self.session.flush()
        except IntegrityError as exc:
            await self.session.rollback()
            raise BackendError("resource_conflict", "An account already exists for this email.", 409) from exc
        return await self._issue(user_id)

    async def login(self, email: str, password: str) -> tuple[str, str]:
        user = await self.session.scalar(select(User).where(User.email == email.strip().lower()))
        if user is None or not password_matches(password, user.password_hash):
            raise BackendError("invalid_credentials", "Email or password is incorrect.", 401)
        return await self._issue(user.id)

    async def _issue(self, user_id: UUID) -> tuple[str, str]:
        access = create_access_token(user_id, self.settings.jwt_secret)
        token_id, refresh = new_refresh_token()
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        self.session.add(
            RefreshToken(
                token_id=token_id,
                user_id=user_id,
                token_hash=token_hash(refresh),
                expires_at=expires,
            )
        )
        await self.session.commit()
        return access, refresh

    async def refresh(self, refresh: str) -> tuple[str, str]:
        token = await self.session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash(refresh))
        )
        if (
            token is None
            or token.revoked
            or token.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc)
        ):
            raise BackendError("authentication_required", "Refresh token is invalid or expired.", 401)
        token.revoked = True
        await self.session.flush()
        return await self._issue(token.user_id)

    async def logout(self, refresh: str) -> None:
        token = await self.session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash(refresh))
        )
        if token is not None:
            token.revoked = True
            await self.session.commit()

    async def delete_account(self, user_id: UUID) -> None:
        user = await self.session.get(User, user_id)
        if user is None:
            raise BackendError("resource_not_found", "Account was not found.", 404)
        await self.session.delete(user)
        await self.session.commit()
