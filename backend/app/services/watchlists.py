from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastcrud import FastCRUD
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BackendError
from app.models.watchlist import Watchlist as WatchlistModel
from app.models.watchlist import WatchlistItem as WatchlistItemModel
from app.schemas.watchlists import (
    Watchlist,
    WatchlistCreate,
    WatchlistCreateRecord,
    WatchlistItem,
    WatchlistItemCreate,
    WatchlistItemCreateRecord,
    WatchlistItemRead,
    WatchlistRead,
)
from app.services.crud import create_record, create_unique
from app.services.instruments import InstrumentService


class WatchlistService:
    def __init__(self, session: AsyncSession, instruments: InstrumentService) -> None:
        self.session = session
        self.instruments = instruments
        self.watchlists: FastCRUD[Any, Any, Any, Any, Any, Any] = FastCRUD(WatchlistModel)
        self.items: FastCRUD[Any, Any, Any, Any, Any, Any] = FastCRUD(WatchlistItemModel)

    async def list(self, user_id: UUID, limit: int, offset: int) -> list[Watchlist]:
        result = await self.watchlists.get_multi(
            db=self.session,
            offset=offset,
            limit=limit,
            schema_to_select=WatchlistRead,
            user_id=user_id,
            sort_columns="created_at",
            sort_orders="asc",
        )
        return [await self._read(item) for item in result["data"]]

    async def get(self, user_id: UUID, watchlist_id: UUID) -> Watchlist:
        record = await self._owned_watchlist(user_id, watchlist_id)
        return await self._read(record)

    async def create(self, user_id: UUID, payload: WatchlistCreate) -> Watchlist:
        record = await create_record(
            self.watchlists,
            self.session,
            WatchlistCreateRecord(
                user_id=user_id,
                name=payload.name,
                created_at=datetime.now(timezone.utc),
            ),
            WatchlistRead,
        )
        return await self._read(record)

    async def delete(self, user_id: UUID, watchlist_id: UUID) -> None:
        await self._owned_watchlist(user_id, watchlist_id)
        await self.watchlists.delete(
            db=self.session,
            where=WatchlistModel.id == watchlist_id,
            user_id=user_id,
        )
        await self.session.commit()

    async def add(self, user_id: UUID, watchlist_id: UUID, payload: WatchlistItemCreate) -> WatchlistItem:
        await self._owned_watchlist(user_id, watchlist_id)
        normalized = await self.instruments.verify_symbol(payload.symbol)
        record = await create_unique(
            self.items,
            self.session,
            WatchlistItemCreateRecord(
                watchlist_id=watchlist_id,
                symbol=normalized,
                created_at=datetime.now(timezone.utc),
            ),
            WatchlistItemRead,
            "This symbol is already in the watchlist.",
        )
        return WatchlistItem.model_validate(record)

    async def remove(self, user_id: UUID, watchlist_id: UUID, item_id: UUID) -> None:
        await self._owned_watchlist(user_id, watchlist_id)
        item = await self.items.get(
            db=self.session,
            schema_to_select=WatchlistItemRead,
            id=item_id,
            watchlist_id=watchlist_id,
        )
        if item is None:
            raise BackendError("resource_not_found", "Watchlist item was not found.", 404)
        await self.items.delete(db=self.session, where=WatchlistItemModel.id == item_id)
        await self.session.commit()

    async def _owned_watchlist(self, user_id: UUID, watchlist_id: UUID) -> WatchlistRead:
        record = await self.watchlists.get(
            db=self.session,
            schema_to_select=WatchlistRead,
            id=watchlist_id,
            user_id=user_id,
        )
        if record is None:
            raise BackendError("resource_not_found", "Watchlist was not found.", 404)
        return WatchlistRead.model_validate(record)

    async def _read(self, record: WatchlistRead | dict[str, object]) -> Watchlist:
        watchlist = WatchlistRead.model_validate(record)
        result = await self.items.get_multi(
            db=self.session,
            schema_to_select=WatchlistItemRead,
            watchlist_id=watchlist.id,
            sort_columns="created_at",
            sort_orders="asc",
        )
        return Watchlist.model_validate(
            {
                **watchlist.model_dump(exclude={"user_id"}),
                "items": [WatchlistItem.model_validate(item) for item in result["data"]],
            }
        )
