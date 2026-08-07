"""Tests for the render service and scene cache."""

from __future__ import annotations

import numpy as np

from app.ai.scene.result import SceneResult
from app.cache.scene_cache import SceneCache
from app.services.render_service import RenderService


class _StubAnalyzer:
    def __init__(self) -> None:
        self.calls = 0
        self.providers = {"detector": "stub", "segmenter": "stub", "depth": "stub"}

    def analyze(self, room_path, progress_cb=None):
        self.calls += 1
        image = np.zeros((200, 300, 3), dtype=np.uint8)
        mask = np.zeros((200, 300), dtype=np.uint8)
        mask[100:, 40:260] = 255
        scene = SceneResult(
            image=image,
            width=300,
            height=200,
            floor_mask=mask,
            floor_polygon=np.array(
                [[60, 100], [240, 100], [280, 199], [20, 199]], dtype=np.float32
            ),
            homography=np.eye(3, dtype=np.float32),
        )
        return scene


def test_render_service_writes_output(room_image_path, tile_image_path, tmp_path):
    cache = SceneCache(root=tmp_path / "scenes")
    analyzer = _StubAnalyzer()
    service = RenderService(analyzer=analyzer, cache=cache)

    out = service.render(
        room_path=room_image_path,
        tile_path=tile_image_path,
        pattern="Chevron",
    )

    import cv2

    from pathlib import Path

    assert Path(out).exists()
    image = cv2.imread(out)
    assert image is not None
    assert image.shape[2] == 3


def test_render_service_caches_scene(room_image_path, tile_image_path, tmp_path):
    cache = SceneCache(root=tmp_path / "scenes")
    analyzer = _StubAnalyzer()
    service = RenderService(analyzer=analyzer, cache=cache)

    service.render(room_path=room_image_path, tile_path=tile_image_path)
    service.render(room_path=room_image_path, tile_path=tile_image_path)

    assert analyzer.calls == 1
    assert cache.exists(service._cache_key(room_image_path))


def test_scene_cache_roundtrip(tmp_path):
    cache = SceneCache(root=tmp_path / "scenes")
    scene = SceneResult(
        image=np.zeros((10, 10, 3), dtype=np.uint8),
        width=10,
        height=10,
        floor_mask=np.ones((10, 10), dtype=np.uint8),
    )
    cache.save("kitchen", scene)

    assert cache.exists("kitchen")
    loaded = cache.load("kitchen")
    assert isinstance(loaded, SceneResult)
    assert loaded.width == 10

    cache.delete("kitchen")
    assert not cache.exists("kitchen")
