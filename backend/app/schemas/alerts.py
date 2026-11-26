from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    operator: Literal["above", "below"]
    threshold: float = Field(gt=0)


class AlertRead(BaseModel):
    id: UUID
    user_id: UUID
    symbol: str
    operator: Literal["above", "below"]
    threshold: float
    active: bool
    created_at: datetime


class Alert(BaseModel):
    id: UUID
    symbol: str
    operator: Literal["above", "below"]
    threshold: float
    active: bool
    created_at: datetime


class DeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    alert_id: UUID
    triggered_price: float
    message: str
    read: bool
    delivered_at: datetime


class DeliveryCreateRecord(BaseModel):
    alert_id: UUID
    triggered_price: float
    message: str
    read: bool
    delivered_at: datetime


class AlertCreateRecord(BaseModel):
    user_id: UUID
    symbol: str
    operator: str
    threshold: float
    active: bool
    created_at: datetime
