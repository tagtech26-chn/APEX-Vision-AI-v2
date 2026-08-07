"""Tile service: resolve tile ids to tile records + image paths."""

from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.services.catalog_service import CatalogService


class TileService:
    """Maps tile ids to catalog entries with a resolved image path."""

    def __init__(
        self,
        catalog: CatalogService | None = None,
        image_root: str | Path | None = None,
    ) -> None:
        self.catalog = catalog or CatalogService()
        self.image_root = Path(image_root) if image_root else settings.tile_images_dir

    def get_tile(self, tile_id: int) -> dict:
        self.catalog.reload()
        tile = self.catalog.get(tile_id)
        if tile is None:
            raise ValueError(f"Tile {tile_id} not found.")

        image = self.image_root / (tile.get("image") or "")
        if not image.exists():
            raise FileNotFoundError(f"Tile image missing: {image}")

        result = dict(tile)
        result["image_path"] = str(image)
        return result
