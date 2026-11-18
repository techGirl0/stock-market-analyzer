from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.db import Database
from app.core.errors import BackendError
from app.schemas.watchlists import Watchlist, WatchlistItem


class WatchlistService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def list(self, user_id: UUID) -> list[Watchlist]:
        with self.database.connection() as connection:
            lists = connection.execute(
                "SELECT id, name, created_at FROM watchlists WHERE user_id = ? ORDER BY created_at",
                (str(user_id),),
            ).fetchall()
            return [self._read(connection, row) for row in lists]

    def create(self, user_id: UUID, name: str) -> Watchlist:
        watchlist_id = uuid4()
        created_at = datetime.now(timezone.utc)
        with self.database.connection() as connection:
            connection.execute(
                "INSERT INTO watchlists (id, user_id, name, created_at) VALUES (?, ?, ?, ?)",
                (str(watchlist_id), str(user_id), name, created_at.isoformat()),
            )
        return Watchlist(id=watchlist_id, name=name, items=[], created_at=created_at)

    def add(self, user_id: UUID, watchlist_id: UUID, symbol: str) -> WatchlistItem:
        normalized = symbol.strip().upper()
        item_id = uuid4()
        created_at = datetime.now(timezone.utc)
        with self.database.connection() as connection:
            owned = connection.execute(
                "SELECT 1 FROM watchlists WHERE id = ? AND user_id = ?",
                (str(watchlist_id), str(user_id)),
            ).fetchone()
            if owned is None:
                raise BackendError("resource_not_found", "Watchlist was not found.", 404)
            try:
                connection.execute(
                    "INSERT INTO watchlist_items (id, watchlist_id, symbol, created_at) VALUES (?, ?, ?, ?)",
                    (str(item_id), str(watchlist_id), normalized, created_at.isoformat()),
                )
            except Exception as exc:
                if "UNIQUE constraint failed" in str(exc):
                    raise BackendError("resource_conflict", "This symbol is already in the watchlist.", 409) from exc
                raise
        return WatchlistItem(id=item_id, symbol=normalized, created_at=created_at)

    def remove(self, user_id: UUID, watchlist_id: UUID, item_id: UUID) -> None:
        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                DELETE FROM watchlist_items
                WHERE id = ? AND watchlist_id IN
                    (SELECT id FROM watchlists WHERE id = ? AND user_id = ?)
                """,
                (str(item_id), str(watchlist_id), str(user_id)),
            )
            if cursor.rowcount == 0:
                raise BackendError("resource_not_found", "Watchlist item was not found.", 404)

    def _read(self, connection, row) -> Watchlist:
        items = connection.execute(
            "SELECT id, symbol, created_at FROM watchlist_items WHERE watchlist_id = ? ORDER BY created_at",
            (row["id"],),
        ).fetchall()
        return Watchlist(
            id=UUID(row["id"]),
            name=row["name"],
            created_at=datetime.fromisoformat(row["created_at"]),
            items=[
                WatchlistItem(
                    id=UUID(item["id"]),
                    symbol=item["symbol"],
                    created_at=datetime.fromisoformat(item["created_at"]),
                )
                for item in items
            ],
        )
