from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Generic, Literal, TypeVar
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


class Availability(str, Enum):
    available = "available"
    stale = "stale"
    partial = "partial"
    unavailable = "unavailable"


class DataMeta(BaseModel):
    source: str
    fetched_at: datetime
    availability: Availability
    delayed: bool


class Instrument(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    symbol: str
    name: str
    exchange: str | None = None
    currency: str | None = None


class InstrumentMatch(Instrument):
    pass


class Quote(BaseModel):
    instrument: Instrument
    price: Decimal | None = None
    previous_close: Decimal | None = None
    change: Decimal | None = None
    change_percent: Decimal | None = None
    volume: int | None = None
    as_of: datetime | None = None
    meta: DataMeta


class Candle(BaseModel):
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int | None = None


class NewsArticle(BaseModel):
    id: UUID
    headline: str
    publisher: str | None = None
    published_at: datetime
    source_url: AnyHttpUrl
    summary: str | None = None
    sentiment: Literal["positive", "negative", "neutral", "unavailable"]
    sentiment_confidence: Decimal | None = None
    meta: DataMeta


class InstrumentDetail(BaseModel):
    instrument: Instrument
    quote: Quote
    meta: DataMeta


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    meta: DataMeta | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: dict[str, Literal["ok", "failed"]]


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


def normalize_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol or len(symbol) > 20:
        raise ValueError("symbol must contain between 1 and 20 characters")
    return symbol


class SymbolPath(BaseModel):
    symbol: str

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        return normalize_symbol(value)
