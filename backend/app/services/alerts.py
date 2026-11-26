from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.connectors.market import MarketDataConnector
from app.core.db import Database
from app.core.errors import BackendError
from app.schemas.alerts import Alert


def _uid(user_id: UUID) -> str:
    # SQLAlchemy stores UUID as hex without dashes; raw sqlite3 must match.
    return user_id.hex


class AlertService:
    def __init__(self, database: Database, market: MarketDataConnector) -> None:
        self.database, self.market = database, market

    def list(self, user_id: UUID) -> list[Alert]:
        with self.database.connection() as c:
            rows = c.execute("SELECT * FROM price_alerts WHERE user_id=? ORDER BY created_at", (_uid(user_id),)).fetchall()
            return [self._model(x) for x in rows]

    async def create(self, user_id: UUID, symbol: str, operator: str, threshold: float) -> Alert:
        symbol = symbol.strip().upper()
        if not await self.market.validate(symbol):
            raise BackendError("ticker_not_found", "The requested instrument was not recognised.", 404)
        aid, now = uuid4(), datetime.now(timezone.utc)
        with self.database.connection() as c:
            c.execute("INSERT INTO price_alerts VALUES (?,?,?,?,?,?,?)", (str(aid), _uid(user_id), symbol, operator, threshold, 1, now.isoformat()))
        return Alert(id=aid, symbol=symbol, operator=operator, threshold=threshold, active=True, created_at=now)

    def delete(self, user_id: UUID, alert_id: UUID) -> None:
        with self.database.connection() as c:
            result = c.execute("DELETE FROM price_alerts WHERE id=? AND user_id=?", (str(alert_id), _uid(user_id)))
            if not result.rowcount:
                raise BackendError("resource_not_found", "Alert was not found.", 404)

    async def evaluate_active(self) -> int:
        """Evaluate active alerts once; delivery uniqueness makes this idempotent."""
        triggered = 0
        with self.database.connection() as c:
            rows = c.execute("SELECT * FROM price_alerts WHERE active=1").fetchall()
        for row in rows:
            quote = await self.market.quote(row["symbol"])
            if quote.price is None:
                continue
            matched = (row["operator"] == "above" and quote.price >= row["threshold"]) or (
                row["operator"] == "below" and quote.price <= row["threshold"]
            )
            if not matched:
                continue
            with self.database.connection() as c:
                try:
                    c.execute(
                        "INSERT INTO alert_deliveries VALUES (?,?,?,?)",
                        (str(uuid4()), row["id"], float(quote.price), datetime.now(timezone.utc).isoformat()),
                    )
                    triggered += 1
                except Exception as exc:
                    if "UNIQUE constraint failed" not in str(exc):
                        raise
        return triggered

    def _model(self, row) -> Alert:
        return Alert(id=UUID(row["id"]), symbol=row["symbol"], operator=row["operator"], threshold=row["threshold"],
                     active=bool(row["active"]), created_at=datetime.fromisoformat(row["created_at"]))
