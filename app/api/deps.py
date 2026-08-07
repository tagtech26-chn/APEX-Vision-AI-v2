"""Shared API dependencies / singletons."""

from __future__ import annotations

from app.core.config import settings
from app.services.catalog_service import CatalogService
from app.services.render_service import RenderService
from app.services.room_service import RoomService
from app.services.tile_service import TileService


class AppServices:
    """Holds lazily-created singletons shared across routes."""

    def __init__(self) -> None:
        self._catalog: CatalogService | None = None
        self._rooms: RoomService | None = None
        self._tiles: TileService | None = None
        self._render: RenderService | None = None

    @property
    def catalog(self) -> CatalogService:
        if self._catalog is None:
            self._catalog = CatalogService()
        return self._catalog

    @property
    def rooms(self) -> RoomService:
        if self._rooms is None:
            self._rooms = RoomService()
        return self._rooms

    @property
    def tiles(self) -> TileService:
        if self._tiles is None:
            self._tiles = TileService(catalog=self.catalog)
        return self._tiles

    @property
    def render(self) -> RenderService:
        if self._render is None:
            self._render = RenderService()
        return self._render


services = AppServices()
settings_ref = settings
