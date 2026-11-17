from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WatchlistCreate(BaseModel):
    name: str = Field(default="My Watchlist", min_length=1, max_length=80)


class WatchlistItemCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)


class WatchlistItem(BaseModel):
    id: UUID
    symbol: str
    created_at: datetime


class Watchlist(BaseModel):
    id: UUID
    name: str
    items: list[WatchlistItem]
    created_at: datetime
