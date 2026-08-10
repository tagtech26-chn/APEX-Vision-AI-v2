"""Deterministic performance smoke tests for the v2.2 rendering baseline."""

from __future__ import annotations

import time

import cv2
import numpy as np

from app.ai.scene.result import SceneResult
from app.renderer.tile_renderer import TileRenderer


def _scene(size: int = 768) -> SceneResult:
    image = np.full((size, size, 3), 180, dtype=np.uint8)
    mask = np.zeros((size, size), dtype=np.uint8)
    cv2.rectangle(mask, (32, 32), (size - 32, size - 32), 255, -1)
    return SceneResult(
        image=image,
        width=size,
        height=size,
        floor_mask=mask,
        homography=np.eye(3, dtype=np.float64),
    )


def test_render_pipeline_performance_baseline() -> None:
    scene = _scene()
    tile = np.full((256, 256, 3), (80, 140, 200), dtype=np.uint8)
    renderer = TileRenderer()

    started = time.perf_counter()
    result = renderer.render(scene=scene, tile=tile, tile_size_mm=600, grout_width=2)
    elapsed = time.perf_counter() - started

    assert result.shape == scene.image.shape
    assert result.dtype == np.uint8
    # A generous CI-safe ceiling: this is a regression guard, not a benchmark target.
    assert elapsed < 5.0, f"render smoke test exceeded 5s: {elapsed:.3f}s"
