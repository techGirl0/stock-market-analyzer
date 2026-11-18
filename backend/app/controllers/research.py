from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.dependencies_research import get_research_service
from app.schemas.research import BriefResponse, ChatRequest, ChatResponse
from app.services.research import ResearchService

router = APIRouter(prefix="/instruments", tags=["research"])

@router.post("/{symbol}/brief", response_model=BriefResponse)
async def brief(symbol: str, _: object = Depends(get_current_user), service: ResearchService = Depends(get_research_service)):
    return await service.brief(symbol)

@router.post("/{symbol}/chat", response_model=ChatResponse)
async def chat(symbol: str, payload: ChatRequest, _: object = Depends(get_current_user), service: ResearchService = Depends(get_research_service)):
    return await service.chat(symbol, payload.messages, payload.user_message)
