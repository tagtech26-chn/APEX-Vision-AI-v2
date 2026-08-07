"""Tests for grout, feathering and the renderer compositor."""

from __future__ import annotations

import numpy as np

from app.ai.scene.result import SceneResult
from app.renderer.grout_engine import GroutEngine
from app.renderer.mask_feather import MaskFeather
from app.renderer.tile_renderer import TileRenderer


def _scene() -> SceneResult:
    h, w = 240, 320
    image = np.zeros((h, w, 3), dtype=np.uint8)
    image[:, :] = (200, 210, 220)

    floor_mask = np.zeros((h, w), dtype=np.uint8)
    floor_mask[120:, 60:260] = 255

    polygon = np.array([[80, 120], [240, 120], [280, 239], [40, 239]], dtype=np.float32)
    homography = np.array(
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float32
    )

    return SceneResult(
        image=image,
        width=w,
        height=h,
        floor_mask=floor_mask,
        floor_polygon=polygon,
        homography=homography,
    )


def _tile() -> np.ndarray:
    tile = np.zeros((96, 96, 3), dtype=np.uint8)
    tile[:, :] = (80, 140, 200)
    return tile


def test_grout_applies_border():
    tile = _tile()
    result = GroutEngine().apply(tile, grout_width_mm=2, grout_color=(220, 220, 220))
    assert result.shape == tile.shape
    # Top-left corner should be grout coloured now.
    np.testing.assert_allclose(result[0, 0], [220, 220, 220])


def test_feather_returns_float_alpha():
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[30:70, 30:70] = 255
    alpha = MaskFeather().feather(mask, radius=11)
    assert alpha.shape == mask.shape
    assert alpha.dtype == np.float32
    assert 0.0 <= alpha.min() <= alpha.max() <= 1.0


def test_renderer_output_shape():
    renderer = TileRenderer()
    result = renderer.render(
        scene=_scene(),
        tile=_tile(),
        tile_size_mm=600,
        pattern="Herringbone",
    )
    assert result.shape == (240, 320, 3)
    assert result.dtype == np.uint8


def test_renderer_requires_scene_parts():
    renderer = TileRenderer()
    scene = _scene()
    scene.homography = None
    try:
        renderer.render(scene=scene, tile=_tile())
        raised = False
    except RuntimeError:
        raised = True
    assert raised


def test_renderer_preserves_furniture_holes():
    """Regions the floor mask carves out must not be painted with tile."""
    scene = _scene()
    # A "rug" hole inside the floor.
    scene.floor_mask[120:200, 80:240] = 0
    # Centre of the hole, away from feathered edges.
    hole_centre = np.zeros(scene.floor_mask.shape, dtype=np.uint8)
    hole_centre[150:170, 130:190] = 255

    renderer = TileRenderer()
    result = renderer.render(scene=scene, tile=_tile(), tile_size_mm=600)

    diff = np.abs(result.astype(int) - scene.image.astype(int)).mean(axis=2)
    # Tiled floor changes; the hole centre keeps the original floor colour.
    assert diff[scene.floor_mask > 0].mean() > 1.0
    assert diff[hole_centre > 0].mean() < 1.0
