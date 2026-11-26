from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.controllers import alerts, analysis, auth, health, instruments, portfolio, research, watchlists
from app.core.config import get_settings
from app.core.errors import (
    BackendError,
    backend_error_handler,
    error_body,
    unhandled_error_handler,
    validation_error_handler,
)
from app.core.rate_limit import FixedWindowLimiter, client_key

settings = get_settings()
api_limiter = FixedWindowLimiter(settings.api_rate_limit, 60)
app = FastAPI(title=settings.app_name, version="1.0.0")
# FastAPI's handler stub requires a broader exception parameter than these handlers.
app.add_exception_handler(BackendError, backend_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_error_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    try:
        api_limiter.check(client_key(request))
    except BackendError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, request_id, exc.details),
        )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(instruments.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(watchlists.router, prefix=settings.api_prefix)
app.include_router(analysis.router, prefix=settings.api_prefix)
app.include_router(research.router, prefix=settings.api_prefix)
app.include_router(portfolio.router, prefix=settings.api_prefix)
app.include_router(alerts.router, prefix=settings.api_prefix)
