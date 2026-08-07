"""Catalog service: loads and serves tile catalog data."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings


class CatalogService:
    """Reads the tile catalog and enriches it with asset URLs."""

    SUPPORTED_KEYS = ("category", "finish", "size", "series")

    def __init__(self, catalog_file: str | Path | None = None) -> None:
        self.catalog_file = Path(catalog_file) if catalog_file else settings.catalog_file
        self.catalog_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.catalog_file.exists():
            self.catalog_file.write_text("[]", encoding="utf-8")

        self.tiles: list[dict] = []
        self.reload()

    def reload(self) -> None:
        with self.catalog_file.open("r", encoding="utf-8") as fp:
            data = json.load(fp)

        if not isinstance(data, list):
            raise ValueError("Catalog must be a JSON array of tiles.")

        self.tiles = []
        for index, tile in enumerate(data, start=1):
            if not isinstance(tile, dict):
                raise ValueError(f"Catalog item {index} is not an object.")
            filename = tile.get("image", "")
            entry = dict(tile)
            entry["imageUrl"] = f"/assets/tiles/images/{filename}"
            entry["thumbnail"] = f"/assets/tiles/thumbnails/{filename}"
            self.tiles.append(entry)

    def all(self) -> list[dict]:
        return self.tiles

    def get(self, tile_id: int) -> dict | None:
        for tile in self.tiles:
            if tile.get("id") == tile_id:
                return tile
        return None

    def values_for(self, key: str) -> list[str]:
        return sorted(
            {t[key] for t in self.tiles if t.get(key)},
        )

    def categories(self) -> list[str]:
        return self.values_for("category")

    def finishes(self) -> list[str]:
        return self.values_for("finish")

    def sizes(self) -> list[str]:
        return self.values_for("size")

    def series(self) -> list[str]:
        return self.values_for("series")
