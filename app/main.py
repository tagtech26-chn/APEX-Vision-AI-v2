"""FastAPI application entry point."""

from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.catalog import router as catalog_router
from app.api.routes.diagnostics import router as diagnostics_router
from app.api.routes.render import router as render_router
from app.api.routes.rooms import router as rooms_router
from app.core.config import settings
from app.core.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("apex")
FRONTEND_DIST = Path(os.getenv("APEX_FRONTEND_DIST", "") or (settings.project_root / "frontend" / "dist"))


def _cors_origins() -> list[str]:
    """Allow local development origins only in debug mode."""
    origins: list[str] = []
    if settings.debug:
        origins.extend(["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173", "http://127.0.0.1:4173"])
    extra = os.getenv("APEX_CORS_ORIGINS", "")
    origins.extend(o.strip() for o in extra.split(",") if o.strip())
    return origins


def _warm_models() -> None:
    if settings.ai_provider not in {"heavy", "auto"}:
        return
    try:
        from app.api.deps import services
        services.render.get_analyzer()
        logger.info("AI models warmed up")
    except Exception:
        logger.exception("AI model warm-up failed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    threading.Thread(target=_warm_models, daemon=True, name="apex-model-warmup").start()
    yield


app = FastAPI(title="APEX Vision AI", version="2.1.0", description="AI floor detection, room segmentation and tile rendering.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=_cors_origins(), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def exception_and_cache_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request failure: %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"success": False, "error": "Internal server error"})
    if request.url.path.startswith("/output/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


app.include_router(rooms_router)
app.include_router(catalog_router)
app.include_router(render_router)
app.include_router(diagnostics_router)
app.mount("/assets", StaticFiles(directory=str(settings.assets_dir)), name="assets")
app.mount("/output", StaticFiles(directory=str(settings.output_dir)), name="output")


@app.get("/api/health")
def health():
    return {"success": True, "status": "ok", "version": "2.1.0"}


@app.get("/api/ready")
def readiness():
    return {"success": True, "status": "ready", "version": "2.1.0"}


if FRONTEND_DIST.is_dir():
    logger.info("Serving frontend from %s", FRONTEND_DIST)
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    logger.warning("frontend/dist not found — running API only")

    @app.get("/")
    def home():
        return {"application": "APEX Vision AI", "status": "Running", "version": "2.1.0", "ai_provider": settings.ai_provider}
