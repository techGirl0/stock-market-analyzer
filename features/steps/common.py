"""Shared helpers for the BDD step definitions."""


def override_instruments(context, connector) -> None:
    """Swap the market-data provider for this scenario.

    environment.py restores the default demo provider after each scenario.
    """
    from app.dependencies import get_instrument_service
    from app.services.instruments import InstrumentService

    context.client.app.dependency_overrides[get_instrument_service] = lambda: InstrumentService(connector)
