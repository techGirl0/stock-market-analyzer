from datetime import datetime
from uuid import UUID
from typing import Literal
from pydantic import BaseModel, Field

class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    operator: Literal["above", "below"]
    threshold: float = Field(gt=0)

class Alert(BaseModel):
    id: UUID
    symbol: str
    operator: Literal["above", "below"]
    threshold: float
    active: bool
    created_at: datetime
