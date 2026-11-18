from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class PortfolioCreate(BaseModel):
    name: str = Field(default="My Portfolio", min_length=1, max_length=80)

class HoldingCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    quantity: float = Field(gt=0)

class Holding(BaseModel):
    id: UUID
    symbol: str
    quantity: float
    current_price: float | None = None
    current_value: float | None = None
    created_at: datetime

class Portfolio(BaseModel):
    id: UUID
    name: str
    holdings: list[Holding]
    total_value: float | None = None
    created_at: datetime
