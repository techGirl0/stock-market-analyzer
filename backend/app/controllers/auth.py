from fastapi import APIRouter, Depends, Request, Response

from app.core.rate_limit import auth_limiter
from app.dependencies import get_current_user
from app.schemas.auth import AuthResponse, Credentials, RefreshRequest
from app.services.auth import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def response(access: str, refresh: str) -> AuthResponse:
    return AuthResponse(access_token=access, refresh_token=refresh)


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    request: Request, payload: Credentials, service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    auth_limiter.check(request.client.host if request.client else "unknown")
    return response(*(await service.register(payload.email, payload.password)))


@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request, payload: Credentials, service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    auth_limiter.check(request.client.host if request.client else "unknown")
    return response(*(await service.login(payload.email, payload.password)))


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    request: Request, payload: RefreshRequest, service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    auth_limiter.check(request.client.host if request.client else "unknown")
    return response(*(await service.refresh(payload.refresh_token)))


@router.post("/logout", status_code=204)
async def logout(
    payload: RefreshRequest,
    _: object = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    await service.logout(payload.refresh_token)
    return Response(status_code=204)


@router.delete("/me", status_code=204)
async def delete_account(
    user_id=Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    await service.delete_account(user_id)
    return Response(status_code=204)
