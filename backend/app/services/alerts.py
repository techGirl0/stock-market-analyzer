import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, List
from uuid import UUID

from fastcrud import FastCRUD
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BackendError
from app.models.alert import AlertDelivery as AlertDeliveryModel
from app.models.alert import PriceAlert as PriceAlertModel
from app.schemas.alerts import Alert, AlertRead, DeliveryCreateRecord, DeliveryRead
from app.services.instruments import InstrumentService

logger = logging.getLogger(__name__)

_READ_DISCLAIMER = "This is a price observation, not investment advice."


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _notification_message(symbol: str, operator: str, threshold: float, price: float) -> str:
    return f"{symbol} is trading at ${price:.2f}, {operator} your ${threshold:.2f} threshold. {_READ_DISCLAIMER}"


class AlertService:
    def __init__(self, session: AsyncSession, instruments: InstrumentService) -> None:
        self.session = session
        self.instruments = instruments
        self.alerts: FastCRUD[Any, Any, Any, Any, Any, Any] = FastCRUD(PriceAlertModel)
        self.deliveries: FastCRUD[Any, Any, Any, Any, Any, Any] = FastCRUD(AlertDeliveryModel)

    async def list(self, user_id: UUID) -> list[Alert]:
        result = await self.alerts.get_multi(
            db=self.session,
            schema_to_select=AlertRead,
            user_id=user_id,
            sort_columns="created_at",
            sort_orders="asc",
            limit=100,
        )
        return [Alert.model_validate(item) for item in result["data"]]

    async def create(self, user_id: UUID, symbol: str, operator: str, threshold: float) -> Alert:
        normalized = symbol.strip().upper()
        try:
            await self.instruments.quote(normalized)
        except BackendError as exc:
            if exc.code == "ticker_not_found":
                raise BackendError("ticker_not_found", f'Ticker "{normalized}" was not found.', 404) from exc
            raise
        record = await self.alerts.create(
            db=self.session,
            object=AlertCreateRecord(
                user_id=user_id,
                symbol=normalized,
                operator=operator,
                threshold=threshold,
                active=True,
                created_at=_default_clock(),
            ),
            schema_to_select=AlertRead,
        )
        await self.session.commit()
        if record is None:
            raise BackendError("internal_error", "Alert could not be created.", 500)
        return Alert.model_validate(record)

    async def delete(self, user_id: UUID, alert_id: UUID) -> None:
        record = await self.alerts.get(
            db=self.session,
            schema_to_select=AlertRead,
            id=alert_id,
            user_id=user_id,
        )
        if record is None:
            raise BackendError("resource_not_found", "Alert was not found.", 404)
        await self.alerts.delete(db=self.session, where=PriceAlertModel.id == alert_id, user_id=user_id)
        await self.session.commit()

    async def notifications(self, user_id: UUID) -> List[DeliveryRead]:
        """List the user's in-app notifications (alert deliveries), newest first."""
        result = await self.session.execute(
            select(AlertDeliveryModel)
            .join(PriceAlertModel, AlertDeliveryModel.alert_id == PriceAlertModel.id)
            .where(PriceAlertModel.user_id == user_id)
            .order_by(AlertDeliveryModel.delivered_at.desc())
            .limit(100)
        )
        return [DeliveryRead.model_validate(row) for row in result.scalars().all()]

    async def mark_read(self, user_id: UUID, delivery_id: UUID) -> DeliveryRead:
        """Mark one of the user's notifications as read (404 if not owned)."""
        result = await self.session.execute(
            select(AlertDeliveryModel)
            .join(PriceAlertModel, AlertDeliveryModel.alert_id == PriceAlertModel.id)
            .where(AlertDeliveryModel.id == delivery_id, PriceAlertModel.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise BackendError("resource_not_found", "Notification was not found.", 404)
        row.read = True
        await self.session.commit()
        return DeliveryRead.model_validate(row)

    async def evaluate_active(
        self,
        clock: Callable[[], datetime] | None = None,
        max_attempts: int = 3,
        backoff_base_seconds: float = 1.0,
    ) -> int:
        """Evaluate active alerts once and create in-app notifications.

        Idempotent: the (alert_id, triggered_price) unique constraint means a
        repeated evaluation at the same price creates exactly one notification.
        Provider failures never create notifications; unavailable prices are
        skipped and logged. Retries use bounded exponential back-off.
        """
        now_fn = clock or _default_clock
        triggered = 0
        result = await self.alerts.get_multi(
            db=self.session,
            schema_to_select=AlertRead,
            active=True,
            limit=1000,
        )
        for alert in result["data"]:
            record = AlertRead.model_validate(alert)
            price = await self._quote_with_retry(record, max_attempts, backoff_base_seconds)
            if price is None:
                continue
            matched = (record.operator == "above" and price >= record.threshold) or (
                record.operator == "below" and price <= record.threshold
            )
            if not matched:
                continue
            try:
                await self.deliveries.create(
                    db=self.session,
                    object=DeliveryCreateRecord(
                        alert_id=record.id,
                        triggered_price=price,
                        message=_notification_message(record.symbol, record.operator, record.threshold, price),
                        read=False,
                        delivered_at=now_fn(),
                    ),
                )
                await self.session.commit()
                triggered += 1
            except Exception as exc:
                await self.session.rollback()
                if "uq_alert_deliveries_alert_triggered_price" in str(exc) or "UNIQUE constraint" in str(exc):
                    continue  # already notified at this price; idempotent no-op
                logger.error("Alert delivery failed for alert_id=%s type=%s", record.id, type(exc).__name__)
                raise
        return triggered

    async def _quote_with_retry(
        self, alert: AlertRead, max_attempts: int, backoff_base_seconds: float
    ) -> float | None:
        """Quote the alert's symbol with bounded exponential back-off.

        Returns the price, or None when the price is unavailable or the
        provider keeps failing (logged with the alert id; no secrets).
        """
        for attempt in range(1, max_attempts + 1):
            try:
                quote = await self.instruments.quote(alert.symbol)
                if quote.price is None:
                    logger.warning(
                        "alert_id=%s symbol=%s: price unavailable; skipped", alert.id, alert.symbol
                    )
                    return None
                return float(quote.price)
            except Exception as exc:
                logger.warning(
                    "alert_id=%s symbol=%s attempt=%d/%d provider error type=%s",
                    alert.id, alert.symbol, attempt, max_attempts, type(exc).__name__,
                )
                if attempt < max_attempts:
                    await asyncio.sleep(backoff_base_seconds * (2 ** (attempt - 1)))
        logger.warning("alert_id=%s symbol=%s: provider failed after %d attempts; skipped",
                       alert.id, alert.symbol, max_attempts)
        return None


class AlertCreateRecord(BaseModel):
    user_id: UUID
    symbol: str
    operator: str
    threshold: float
    active: bool
    created_at: datetime
