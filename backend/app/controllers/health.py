from fastapi import APIRouter

from app.schemas.v1 import HealthResponse, ReadinessResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
async def live() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
async def ready() -> ReadinessResponse:
    return ReadinessResponse(status="ready", checks={"application": "ok"})
