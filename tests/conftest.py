"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _write_room(tmp_path: Path, name: str = "room.png") -> Path:
    """Build a synthetic image with a distinct floor region."""
    import cv2

    h, w = 480, 640
    image = np.zeros((h, w, 3), dtype=np.uint8)
    image[:, :] = (200, 210, 220)  # walls

    # Floor: bottom trapezoid.
    pts = np.array([[140, 420], [500, 420], [620, 479], [20, 479]], dtype=np.int32)
    cv2.fillConvexPoly(image, pts, (90, 120, 150))

    path = tmp_path / name
    cv2.imwrite(str(path), image)
    return path


@pytest.fixture
def room_image_path(tmp_path):
    return _write_room(tmp_path)


@pytest.fixture
def tile_image_path(tmp_path):
    import cv2

    tile = np.zeros((128, 128, 3), dtype=np.uint8)
    tile[:, :] = (80, 140, 200)
    cv2.circle(tile, (64, 64), 30, (30, 60, 100), -1)
    path = tmp_path / "tile.jpg"
    cv2.imwrite(str(path), tile)
    return path
