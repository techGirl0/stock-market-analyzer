from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_instrument_service
from app.schemas.v1 import HistoryResponse, InstrumentMatch, Page, Quote
from app.services.instruments import InstrumentService

router = APIRouter(prefix="/instruments", tags=["instruments"])


@router.get("/search", response_model=Page[InstrumentMatch])
async def search_instruments(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=10, ge=1, le=50),
    service: InstrumentService = Depends(get_instrument_service),
) -> Page[InstrumentMatch]:
    return await service.search(q, limit)


@router.get("/{symbol}/quote", response_model=Quote)
async def get_quote(
    symbol: str,
    service: InstrumentService = Depends(get_instrument_service),
) -> Quote:
    return await service.quote(symbol)


@router.get("/{symbol}/history", response_model=HistoryResponse)
async def get_history(
    symbol: str,
    start: datetime | None = None,
    end: datetime | None = None,
    interval: str = Query(default="1d", pattern=r"^(1m|5m|15m|1h|1d)$"),
    limit: int = Query(default=100, ge=1, le=500),
    service: InstrumentService = Depends(get_instrument_service),
) -> HistoryResponse:
    return await service.history(symbol, start, end, interval, limit)

