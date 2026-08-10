from __future__ import annotations

import numpy as np

from app.ai.scene.result import SceneResult
from app.renderer.tile_projector import TileProjector


def test_scene_result_carries_protected_object_mask() -> None:
    scene = SceneResult(width=4, height=4)
    scene.protected_object_mask = np.zeros((4, 4), dtype=np.uint8)
    scene.protected_object_mask[1:3, 1:3] = 255

    assert scene.protected_object_mask.shape == (4, 4)
    assert int((scene.protected_object_mask > 0).sum()) == 4


def test_projector_preserves_protected_region_during_blend() -> None:
    room = np.zeros((16, 16, 3), dtype=np.uint8)
    projection = np.full((16, 16, 3), 255, dtype=np.uint8)
    floor = np.full((16, 16), 255, dtype=np.uint8)
    protected = np.zeros((16, 16), dtype=np.uint8)
    protected[6:10, 6:10] = 255

    result = TileProjector().blend(
        room=room,
        projection=projection,
        floor_mask=floor,
        alpha=1.0,
        occlusion_mask=protected,
    )

    assert np.all(result[6:10, 6:10] == 0)
    assert np.any(result[:6] > 0)


def test_projector_without_occlusion_remains_backward_compatible() -> None:
    room = np.zeros((8, 8, 3), dtype=np.uint8)
    projection = np.full((8, 8, 3), 255, dtype=np.uint8)
    floor = np.full((8, 8), 255, dtype=np.uint8)

    result = TileProjector().blend(
        room=room,
        projection=projection,
        floor_mask=floor,
        alpha=1.0,
    )

    assert np.any(result > 0)
