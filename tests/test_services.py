"""Tests for catalog / room / tile services."""

from __future__ import annotations

import json

import pytest

from app.services.catalog_service import CatalogService
from app.services.room_service import RoomService
from app.services.tile_service import TileService


def _catalog(tmp_path):
    path = tmp_path / "catalog" / "tiles.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            [
                {"id": 1, "name": "A", "category": "Stone", "finish": "Matt",
                 "size": "600x600", "series": "S1", "image": "a.jpg"},
                {"id": 2, "name": "B", "category": "Wood", "finish": "Gloss",
                 "size": "1200x200", "series": "S2", "image": "b.jpg"},
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_catalog_builds_urls(tmp_path):
    catalog = CatalogService(catalog_file=_catalog(tmp_path))
    tiles = catalog.all()
    assert len(tiles) == 2
    assert tiles[0]["imageUrl"] == "/assets/tiles/images/a.jpg"
    assert tiles[0]["thumbnail"] == "/assets/tiles/thumbnails/a.jpg"


def test_catalog_filter_lists(tmp_path):
    catalog = CatalogService(catalog_file=_catalog(tmp_path))
    assert catalog.categories() == ["Stone", "Wood"]
    assert catalog.finishes() == ["Gloss", "Matt"]
    assert catalog.sizes() == ["1200x200", "600x600"]
    assert catalog.series() == ["S1", "S2"]


def test_catalog_get(tmp_path):
    catalog = CatalogService(catalog_file=_catalog(tmp_path))
    assert catalog.get(1)["name"] == "A"
    assert catalog.get(99) is None


def test_room_service_lists_and_resolves(tmp_path):
    (tmp_path / "one.png").write_bytes(b"x")
    (tmp_path / "two.jpg").write_bytes(b"y")
    (tmp_path / "notes.txt").write_text("ignore me")

    service = RoomService(room_root=tmp_path)
    rooms = service.list_rooms()
    assert [r["id"] for r in rooms] == [1, 2]
    assert service.get_room(1).exists()
    assert service.get_room(2).exists()


def test_room_service_invalid_id(tmp_path):
    service = RoomService(room_root=tmp_path)
    with pytest.raises(ValueError):
        service.get_room(5)


def test_tile_service_resolves_image(tmp_path):
    image_root = tmp_path / "images"
    image_root.mkdir()
    (image_root / "a.jpg").write_bytes(b"x")

    catalog = CatalogService(catalog_file=_catalog(tmp_path))
    service = TileService(catalog=catalog, image_root=image_root)
    tile = service.get_tile(1)
    assert tile["image_path"] == str(image_root / "a.jpg")


def test_tile_service_missing_image(tmp_path):
    catalog = CatalogService(catalog_file=_catalog(tmp_path))
    service = TileService(catalog=catalog, image_root=tmp_path)
    with pytest.raises(ValueError):
        service.get_tile(99)
