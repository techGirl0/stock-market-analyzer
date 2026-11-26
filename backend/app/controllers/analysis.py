from fastapi import APIRouter, Depends, Query

from app.dependencies import get_analysis_service, get_current_user
from app.schemas.analysis import ForecastResponse, RiskProfile
from app.services.analysis import AnalysisService
from app.services.finance import HORIZONS

router = APIRouter(prefix="/instruments", tags=["analysis"])

@router.get("/{symbol}/risk", response_model=RiskProfile)
async def risk(
    symbol: str,
    _: object = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    return await service.risk(symbol)

@router.get("/{symbol}/forecast", response_model=ForecastResponse)
async def forecast(
    symbol: str,
    horizon: str = Query(default="20d", pattern="^(" + "|".join(HORIZONS) + ")$"),
    _: object = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    return await service.forecast(symbol, horizon)
