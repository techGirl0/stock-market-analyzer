from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.dependencies_research import get_research_service
from app.schemas.research import BriefResponse, ChatRequest, ChatResponse, ExplainResponse
from app.services.research import ResearchService

router = APIRouter(prefix="/instruments", tags=["research"])


@router.post("/{symbol}/brief", response_model=BriefResponse)
async def brief(
    symbol: str,
    _: object = Depends(get_current_user),
    service: ResearchService = Depends(get_research_service),
):
    return await service.brief(symbol)


@router.post("/{symbol}/chat", response_model=ChatResponse)
async def chat(
    symbol: str,
    payload: ChatRequest,
    _: object = Depends(get_current_user),
    service: ResearchService = Depends(get_research_service),
):
    return await service.chat(symbol, payload.messages, payload.user_message)


@router.post("/{symbol}/explain/risk", response_model=ExplainResponse)
async def explain_risk(
    symbol: str,
    _: object = Depends(get_current_user),
    service: ResearchService = Depends(get_research_service),
):
    return await service.explain_risk(symbol)


@router.post("/{symbol}/explain/volatility", response_model=ExplainResponse)
async def explain_volatility(
    symbol: str,
    _: object = Depends(get_current_user),
    service: ResearchService = Depends(get_research_service),
):
    return await service.explain_volatility(symbol)


@router.post("/{symbol}/explain/scenarios", response_model=ExplainResponse)
async def explain_scenarios(
    symbol: str,
    _: object = Depends(get_current_user),
    service: ResearchService = Depends(get_research_service),
):
    return await service.explain_scenarios(symbol)
