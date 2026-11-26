from uuid import UUID
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_portfolio_service
from app.schemas.portfolio import Portfolio, PortfolioCreate, Holding, HoldingCreate
from app.services.portfolio import PortfolioService

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

@router.get("", response_model=list[Portfolio])
async def list_portfolios(user_id: UUID = Depends(get_current_user), service: PortfolioService = Depends(get_portfolio_service)):
    return await service.list(user_id)

@router.post("", response_model=Portfolio, status_code=201)
async def create_portfolio(payload: PortfolioCreate, user_id: UUID = Depends(get_current_user), service: PortfolioService = Depends(get_portfolio_service)):
    return await service.create(user_id, payload.name)


@router.get("/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(
    portfolio_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
):
    return await service.get(user_id, portfolio_id)

@router.post("/{portfolio_id}/holdings", response_model=Holding, status_code=201)
async def add_holding(portfolio_id: UUID, payload: HoldingCreate, user_id: UUID = Depends(get_current_user), service: PortfolioService = Depends(get_portfolio_service)):
    return await service.add(user_id, portfolio_id, payload.symbol, payload.quantity)
