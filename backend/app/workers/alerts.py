"""Alert evaluation worker (SCRUM-68).

Runs OUTSIDE the request path: a scheduler, queue consumer or CLI entry
point calls run_alert_evaluation(). The worker owns its database session
(it does not borrow the request-scoped one), is idempotent thanks to the
(alert_id, triggered_price) unique constraint, retries provider calls
with bounded exponential back-off and logs failures with the alert id
only — never secrets.
"""

import asyncio
import logging

from app.core.database import async_sessionmaker_factory
from app.services.alerts import AlertService

logger = logging.getLogger(__name__)


async def evaluate_alerts_once() -> int:
    """Run one idempotent alert evaluation cycle; returns notifications created."""
    from app.dependencies import get_instrument_service

    async with async_sessionmaker_factory() as session:
        service = AlertService(session, get_instrument_service())
        try:
            return await service.evaluate_active()
        except Exception as exc:
            logger.error("Alert evaluation cycle failed: type=%s", type(exc).__name__)
            raise


def run_alert_evaluation() -> int:
    """Synchronous entry point for a scheduler or separate process."""
    return asyncio.run(evaluate_alerts_once())
