from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WatchlistCreate(BaseModel):
    name: str = Field(default="My Watchlist", min_length=1, max_length=80)


class WatchlistItemCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)


class WatchlistItemRead(BaseModel):
    id: UUID
    watchlist_id: UUID
    symbol: str
    created_at: datetime


class WatchlistItem(BaseModel):
    id: UUID
    symbol: str
    created_at: datetime


class Watchlist(BaseModel):
    id: UUID
    name: str
    items: list[WatchlistItem]
    created_at: datetime


class WatchlistRead(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime


class WatchlistCreateRecord(BaseModel):
    user_id: UUID
    name: str
    created_at: datetime


class WatchlistItemCreateRecord(BaseModel):
    watchlist_id: UUID
    symbol: str
    created_at: datetime
