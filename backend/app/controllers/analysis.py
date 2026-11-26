from fastapi import APIRouter, Depends, Query
from app.dependencies import get_analysis_service
from app.schemas.analysis import ForecastResponse, RiskProfile
from app.services.analysis import AnalysisService

router = APIRouter(prefix="/instruments", tags=["analysis"])

@router.get("/{symbol}/risk", response_model=RiskProfile)
async def risk(symbol: str, service: AnalysisService = Depends(get_analysis_service)):
    return await service.risk(symbol)

@router.get("/{symbol}/forecast", response_model=ForecastResponse)
async def forecast(symbol: str, horizon: str = Query(default="20d", pattern=r"^(5d|10d|20d|1y|3y|5y)$"),
                   service: AnalysisService = Depends(get_analysis_service)):
    return await service.forecast(symbol, horizon)
