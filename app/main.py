import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    error_payload,
    http_exception_handler,
    validation_exception_handler,
)
from app.db.base import Base
from app.db.session import engine
from app.core.logging import configure_logging
from app.utils.monitoring import REQUEST_COUNT, REQUEST_LATENCY

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(api_router, prefix=settings.api_v1_prefix)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

from fastapi import HTTPException  # noqa: E402

app.add_exception_handler(HTTPException, http_exception_handler)


@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    start = time.perf_counter()
    path = request.url.path
    method = request.method

    try:
        response = await call_next(request)
    except Exception as exc:
        REQUEST_COUNT.labels(method=method, path=path, status=500).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(time.perf_counter() - start)
        logger.exception(
            "unhandled_exception",
            extra={"path": path, "method": method, "error": str(exc)},
        )
        return JSONResponse(status_code=500, content=error_payload("Internal server error", "internal_error"))

    duration = time.perf_counter() - start
    REQUEST_COUNT.labels(method=method, path=path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
    logger.info(
        "request",
        extra={
            "method": method,
            "path": path,
            "status": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        },
    )
    return response


@app.get("/health") 
async def health() -> dict:
    return {"status": "ok", "environment": settings.environment}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
