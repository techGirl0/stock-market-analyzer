import asyncio

from app.dependencies_extra import get_alert_service


async def evaluate_alerts_once() -> int:
    """Run one idempotent alert evaluation cycle for a scheduler or queue."""
    return await get_alert_service().evaluate_active()


def run_alert_evaluation() -> int:
    return asyncio.run(evaluate_alerts_once())
