from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PortfolioCreate(BaseModel):
    name: str = Field(default="My Portfolio", min_length=1, max_length=80)

class HoldingCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    quantity: float = Field(gt=0)

class PortfolioRead(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime

class HoldingRead(BaseModel):
    id: UUID
    portfolio_id: UUID
    symbol: str
    quantity: float
    created_at: datetime

class Holding(BaseModel):
    id: UUID
    symbol: str
    quantity: float
    current_price: float | None = None
    current_value: float | None = None
    price_source: str | None = None
    price_as_of: datetime | None = None
    created_at: datetime

class Portfolio(BaseModel):
    id: UUID
    name: str
    holdings: list[Holding]
    total_value: float | None = None
    value_as_of: datetime | None = None
    created_at: datetime
