"""FastAPI application entry point."""

from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.catalog import router as catalog_router
from app.api.routes.render import router as render_router
from app.api.routes.rooms import router as rooms_router
from app.core.config import settings

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger("apex")

# Path to the built React app. When present, the API and the SPA are served
# from the same process on a single port (production mode). Point APEX_FRONTEND_DIST
# elsewhere to serve a build from a different location.
FRONTEND_DIST = Path(
    os.getenv("APEX_FRONTEND_DIST", "")
    or (settings.project_root / "frontend" / "dist")
)


def _cors_origins() -> list[str]:
    """Development origins plus any APEX_CORS_ORIGINS override (comma-separated)."""
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]
    extra = os.getenv("APEX_CORS_ORIGINS", "")
    origins.extend(o.strip() for o in extra.split(",") if o.strip())
    return origins


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
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rooms_router)
app.include_router(catalog_router)
app.include_router(render_router)

app.mount("/assets", StaticFiles(directory=str(settings.assets_dir)), name="assets")
app.mount("/output", StaticFiles(directory=str(settings.output_dir)), name="output")


@app.get("/api/health")
def health():
    return {"success": True, "status": "ok"}


@app.middleware("http")
async def no_cache_renders(request, call_next):
    """Keep freshly rendered room images from being served from browser caches."""
    response = await call_next(request)
    if request.url.path.startswith("/output/"):
        response.headers["Cache-Control"] = "no-store"
    return response


if FRONTEND_DIST.is_dir():
    # Production mode: serve the built React app as the SPA. Registered last so
    # /api/*, /assets and /output keep their dedicated handlers.
    logger.info("Serving frontend from %s", FRONTEND_DIST)
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    logger.warning(
        "frontend/dist not found — running API only. "
        "Run `npm run build` inside frontend/ to enable the web UI."
    )

    @app.get("/")
    def home():
        return {
            "application": "APEX Vision AI",
            "status": "Running",
            "version": "2.0.0",
            "ai_provider": settings.ai_provider,
        }
