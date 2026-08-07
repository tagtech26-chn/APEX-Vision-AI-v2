"""FastAPI application entry point."""

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.catalog import router as catalog_router
from app.api.routes.render import router as render_router
from app.api.routes.rooms import router as rooms_router
from app.core.config import settings

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger("apex")


def _warm_models() -> None:
    """Load the heavy AI models in the background so the first render is fast."""
    if settings.ai_provider not in {"heavy", "auto"}:
        return
    try:
        from app.api.deps import services

        services.render.get_analyzer()
        logger.info("AI models warmed up.")
    except Exception as exc:  # pragma: no cover - depends on the machine
        logger.warning("AI model warm-up failed: %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    threading.Thread(target=_warm_models, daemon=True).start()
    yield


app = FastAPI(
    title="APEX Vision AI",
    version="2.0.0",
    description="AI floor detection, room segmentation and tile rendering.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rooms_router)
app.include_router(catalog_router)
app.include_router(render_router)

app.mount("/assets", StaticFiles(directory=str(settings.assets_dir)), name="assets")
app.mount("/output", StaticFiles(directory=str(settings.output_dir)), name="output")


@app.middleware("http")
async def no_cache_renders(request, call_next):
    """Keep freshly rendered room images from being served from browser caches."""
    response = await call_next(request)
    if request.url.path.startswith("/output/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def home():
    return {
        "application": "APEX Vision AI",
        "status": "Running",
        "version": "2.0.0",
        "ai_provider": settings.ai_provider,
    }


@app.get("/api/health")
def health():
    return {"success": True, "status": "ok"}
