"""Tile catalog endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import services

router = APIRouter(prefix="/api/catalog", tags=["Catalog"])


@router.get("/tiles")
def tiles():
    return services.catalog.all()


@router.get("/tiles/{tile_id}")
def tile_detail(tile_id: int):
    tile = services.catalog.get(tile_id)
    if tile is None:
        raise HTTPException(status_code=404, detail=f"Tile {tile_id} not found.")
    return tile


@router.get("/categories")
def categories():
    return services.catalog.categories()


@router.get("/finishes")
def finishes():
    return services.catalog.finishes()


@router.get("/sizes")
def sizes():
    return services.catalog.sizes()


@router.get("/series")
def series():
    return services.catalog.series()
