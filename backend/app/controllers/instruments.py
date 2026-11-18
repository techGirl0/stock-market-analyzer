from fastapi import APIRouter, Depends, Query

from app.dependencies import get_instrument_service
from app.schemas.v1 import InstrumentMatch, Page, Quote
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
