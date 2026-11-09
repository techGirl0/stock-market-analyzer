from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from uuid import uuid4

from app.controllers import alerts, analysis, auth, health, instruments, portfolio, research, watchlists
from app.core.config import get_settings
from app.core.errors import (
    BackendError,
    backend_error_handler,
    validation_error_handler,
    unhandled_error_handler,
)

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_exception_handler(BackendError, backend_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
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
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(instruments.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(watchlists.router, prefix=settings.api_prefix)
app.include_router(portfolio.router, prefix=settings.api_prefix)
app.include_router(alerts.router, prefix=settings.api_prefix)
app.include_router(research.router, prefix=settings.api_prefix)
app.include_router(analysis.router, prefix=settings.api_prefix)
