from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    operator: Mapped[str] = mapped_column(String(10), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="alerts")
    deliveries: Mapped[list["AlertDelivery"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan", passive_deletes=True
    )


class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"
    __table_args__ = (
        # One notification per alert and trigger price: re-evaluating the same
        # condition at the same observed price is a no-op (idempotency).
        UniqueConstraint("alert_id", "triggered_price", name="uq_alert_deliveries_alert_triggered_price"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    alert_id: Mapped[UUID] = mapped_column(
        ForeignKey("price_alerts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    triggered_price: Mapped[float] = mapped_column(Float, nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    alert: Mapped["PriceAlert"] = relationship(back_populates="deliveries")
