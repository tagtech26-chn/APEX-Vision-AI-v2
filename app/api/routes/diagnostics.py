"""Operational diagnostics for APEX Vision AI."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import services
from app.core.config import settings
from app.core.metrics import render_metrics

router = APIRouter(prefix="/api/diagnostics", tags=["Diagnostics"])


@router.get("")
def diagnostics():
    """Return safe runtime diagnostics without exposing model paths or secrets."""
    analyzer_loaded = services.render.analyzer is not None
    providers = {}
    if analyzer_loaded:
        providers = services.render.get_analyzer().providers

    return {
        "success": True,
        "application": "APEX Vision AI",
        "version": settings.app_version,
        "ai": {
            "configured_provider": settings.ai_provider,
            "analyzer_loaded": analyzer_loaded,
            "providers": providers,
        },
        "cache": {
            "enabled": services.render.cache.enabled,
            "signing_key_configured": services.render.cache.enabled,
        },
        "render": render_metrics.snapshot(),
    }
