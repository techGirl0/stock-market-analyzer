from datetime import datetime

from pydantic import BaseModel

from app.schemas.v1 import Availability


class AnalysisMeta(BaseModel):
    availability: Availability
    calculated_at: datetime
    calculation_version: str
    assumptions: list[str]
    disclaimer: str

class Scenario(BaseModel):
    label: str
    bear: float
    base: float
    bull: float

class RiskProfile(BaseModel):
    score: int | None
    components: dict[str, str | float | None]
    meta: AnalysisMeta

class ForecastResponse(BaseModel):
    horizon: str
    scenarios: list[dict[str, float]]
    meta: AnalysisMeta
