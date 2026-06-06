from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.app.api.routes.bug_report import router as bug_report_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.result import router as result_router
from backend.app.api.routes.upload import router as upload_router
from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import configure_logging
from backend.app.offers.loader import OffersLoader
from backend.app.services.ttl_cache import TTLCache


_FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = settings
        app.state.profile_cache = TTLCache(default_ttl_seconds=settings.profile_redis_ttl)
        app.state.offers_loader = OffersLoader(settings.artifact_dir / "offers.jsonl")
        loaded = app.state.offers_loader.reload()
        logger.info("offers_loaded", extra={"count": loaded})
        yield

    app = FastAPI(
        title=settings.app_name,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )
    app.add_middleware(GZipMiddleware, minimum_size=1_000)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        max_age=600,
    )
    app.middleware("http")(request_logging_middleware)
    app.include_router(health_router)
    app.include_router(upload_router)
    app.include_router(result_router)
    app.include_router(bug_report_router)

    if _FRONTEND_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=_FRONTEND_DIR), name="static")

        @app.get("/", include_in_schema=False)
        async def index() -> FileResponse:
            return FileResponse(_FRONTEND_DIR / "index.html")

    return app


async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed", extra={"path": request.url.path, "method": request.method})
        raise
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["x-response-time-ms"] = str(elapsed_ms)
    logger.info(
        "request_completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
        },
    )
    return response


app = create_app()
