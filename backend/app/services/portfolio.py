import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4
from app.core.db import Database
from app.core.errors import BackendError
from app.connectors.market import MarketDataConnector

logger = logging.getLogger(__name__)
from app.schemas.portfolio import Holding, Portfolio

class PortfolioService:
    def __init__(self, database: Database, market: MarketDataConnector) -> None:
        self.database, self.market = database, market

    async def list(self, user_id: UUID) -> list[Portfolio]:
        with self.database.connection() as c:
            rows = c.execute("SELECT * FROM portfolios WHERE user_id=? ORDER BY created_at", (str(user_id),)).fetchall()
            return [await self._read(c, row) for row in rows]

    async def create(self, user_id: UUID, name: str) -> Portfolio:
        pid, now = uuid4(), datetime.now(timezone.utc)
        with self.database.connection() as c:
            c.execute("INSERT INTO portfolios VALUES (?,?,?,?)", (str(pid), str(user_id), name, now.isoformat()))
        return Portfolio(id=pid, name=name, holdings=[], total_value=0, created_at=now)

    async def get(self, user_id: UUID, portfolio_id: UUID) -> Portfolio:
        with self.database.connection() as c:
            row = c.execute(
                "SELECT * FROM portfolios WHERE id=? AND user_id=?",
                (str(portfolio_id), str(user_id)),
            ).fetchone()
            if row is None:
                raise BackendError("resource_not_found", "Portfolio was not found.", 404)
            return await self._read(c, row)

    async def add(self, user_id: UUID, portfolio_id: UUID, symbol: str, quantity: float) -> Holding:
        symbol = symbol.strip().upper()
        if not await self.market.validate(symbol):
            raise BackendError("ticker_not_found", "The requested instrument was not recognised.", 404)
        hid, now = uuid4(), datetime.now(timezone.utc)
        with self.database.connection() as c:
            owned = c.execute("SELECT 1 FROM portfolios WHERE id=? AND user_id=?", (str(portfolio_id), str(user_id))).fetchone()
            if not owned:
                raise BackendError("resource_not_found", "Portfolio was not found.", 404)
            try:
                c.execute("INSERT INTO portfolio_holdings VALUES (?,?,?,?,?)", (str(hid), str(portfolio_id), symbol, quantity, now.isoformat()))
            except Exception as exc:
                if "UNIQUE constraint failed" in str(exc):
                    raise BackendError("resource_conflict", "This instrument is already in the portfolio.", 409) from exc
                raise
        return await self._holding(hid, symbol, quantity, now)

    async def _holding(self, hid, symbol, quantity, created_at) -> Holding:
        try:
            quote = await self.market.quote(symbol)
            price = float(quote.price) if quote.price is not None else None
        except Exception:
            logger.warning("Price fetch failed for %s; value will be unavailable", symbol)
            price = None
        return Holding(id=hid, symbol=symbol, quantity=quantity, current_price=price,
                       current_value=price * quantity if price is not None else None, created_at=created_at)

    async def _read(self, c, row) -> Portfolio:
        items = c.execute("SELECT * FROM portfolio_holdings WHERE portfolio_id=? ORDER BY created_at", (row["id"],)).fetchall()
        holdings = [await self._holding(UUID(x["id"]), x["symbol"], x["quantity"], datetime.fromisoformat(x["created_at"])) for x in items]
        total = sum(x.current_value or 0 for x in holdings) if all(x.current_value is not None for x in holdings) else None
        return Portfolio(id=UUID(row["id"]), name=row["name"], holdings=holdings, total_value=total,
                         created_at=datetime.fromisoformat(row["created_at"]))
