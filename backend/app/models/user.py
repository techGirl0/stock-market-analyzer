from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.alert import PriceAlert
    from app.models.portfolio import Portfolio
    from app.models.refresh_token import RefreshToken
    from app.models.watchlist import Watchlist


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    watchlists: Mapped[list["Watchlist"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    portfolios: Mapped[list["Portfolio"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    alerts: Mapped[list["PriceAlert"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
