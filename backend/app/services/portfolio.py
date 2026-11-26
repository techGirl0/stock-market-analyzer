import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastcrud import FastCRUD
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BackendError
from app.models.portfolio import Portfolio as PortfolioModel
from app.models.portfolio import PortfolioHolding as PortfolioHoldingModel
from app.schemas.portfolio import (
    Holding,
    HoldingCreateRecord,
    HoldingRead,
    Portfolio,
    PortfolioCreateRecord,
    PortfolioRead,
)
from app.services.crud import create_record, create_unique
from app.services.instruments import InstrumentService

logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self, session: AsyncSession, instruments: InstrumentService) -> None:
        self.session = session
        self.instruments = instruments
        self.portfolios: FastCRUD[Any, Any, Any, Any, Any, Any] = FastCRUD(PortfolioModel)
        self.holdings: FastCRUD[Any, Any, Any, Any, Any, Any] = FastCRUD(PortfolioHoldingModel)

    async def list(self, user_id: UUID) -> list[Portfolio]:
        result = await self.portfolios.get_multi(
            db=self.session,
            schema_to_select=PortfolioRead,
            user_id=user_id,
            sort_columns="created_at",
            sort_orders="asc",
            limit=100,
        )
        return [await self._read(item) for item in result["data"]]

    async def create(self, user_id: UUID, name: str) -> Portfolio:
        record = await create_record(
            self.portfolios,
            self.session,
            PortfolioCreateRecord(
                user_id=user_id,
                name=name,
                created_at=datetime.now(timezone.utc),
            ),
            PortfolioRead,
        )
        return await self._read(record)

    async def get(self, user_id: UUID, portfolio_id: UUID) -> Portfolio:
        return await self._read(await self._owned(user_id, portfolio_id))

    async def delete(self, user_id: UUID, portfolio_id: UUID) -> None:
        await self._owned(user_id, portfolio_id)
        await self.portfolios.delete(
            db=self.session,
            where=PortfolioModel.id == portfolio_id,
            user_id=user_id,
        )
        await self.session.commit()

    async def add(self, user_id: UUID, portfolio_id: UUID, symbol: str, quantity: float) -> Holding:
        await self._owned(user_id, portfolio_id)
        normalized = await self.instruments.verify_symbol(symbol)
        record = await create_unique(
            self.holdings,
            self.session,
            HoldingCreateRecord(
                portfolio_id=portfolio_id,
                symbol=normalized,
                quantity=quantity,
                created_at=datetime.now(timezone.utc),
            ),
            HoldingRead,
            "This instrument is already in the portfolio.",
        )
        return await self._valued_holding(HoldingRead.model_validate(record))

    async def remove(self, user_id: UUID, portfolio_id: UUID, holding_id: UUID) -> None:
        await self._owned(user_id, portfolio_id)
        record = await self.holdings.get(
            db=self.session,
            schema_to_select=HoldingRead,
            id=holding_id,
            portfolio_id=portfolio_id,
        )
        if record is None:
            raise BackendError("resource_not_found", "Holding was not found.", 404)
        await self.holdings.delete(db=self.session, where=PortfolioHoldingModel.id == holding_id)
        await self.session.commit()

    async def _owned(self, user_id: UUID, portfolio_id: UUID) -> PortfolioRead:
        record = await self.portfolios.get(
            db=self.session,
            schema_to_select=PortfolioRead,
            id=portfolio_id,
            user_id=user_id,
        )
        if record is None:
            raise BackendError("resource_not_found", "Portfolio was not found.", 404)
        return PortfolioRead.model_validate(record)

    async def _valued_holding(self, holding: HoldingRead) -> Holding:
        """Value a holding from the latest available price; unavailable is reported, never defaulted."""
        price = source = as_of = None
        try:
            quote = await self.instruments.quote(holding.symbol)
            if quote.price is not None:
                price = float(quote.price)
                source = quote.meta.source
                as_of = quote.as_of or quote.meta.fetched_at
        except Exception:
            logger.warning("Price fetch failed for %s; value will be unavailable", holding.symbol)
        return Holding.model_validate(
            {
                **holding.model_dump(exclude={"portfolio_id"}),
                "current_price": price,
                "current_value": price * holding.quantity if price is not None else None,
                "price_source": source,
                "price_as_of": as_of,
            }
        )

    async def _read(self, record: PortfolioRead | dict[str, object]) -> Portfolio:
        portfolio = PortfolioRead.model_validate(record)
        result = await self.holdings.get_multi(
            db=self.session,
            schema_to_select=HoldingRead,
            portfolio_id=portfolio.id,
            sort_columns="created_at",
            sort_orders="asc",
            limit=1000,
        )
        holdings = [await self._valued_holding(HoldingRead.model_validate(item)) for item in result["data"]]
        total_value: float | None = None
        value_as_of = None
        if holdings and all(h.current_value is not None for h in holdings):
            total_value = sum(h.current_value or 0.0 for h in holdings)
            value_as_of = max(h.price_as_of for h in holdings if h.price_as_of is not None)
        return Portfolio.model_validate(
            {
                **portfolio.model_dump(exclude={"user_id"}),
                "holdings": holdings,
                "total_value": total_value,
                "value_as_of": value_as_of,
            }
        )
