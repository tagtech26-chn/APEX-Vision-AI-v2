"""Tests for the tile pattern generators."""

from __future__ import annotations

import numpy as np

from app.renderer.patterns import TilePatterns

PATTERNS = ["Straight", "Brick", "Herringbone", "Chevron"]


def _tile() -> np.ndarray:
    tile = np.zeros((64, 64, 3), dtype=np.uint8)
    tile[:, :] = (200, 200, 200)
    tile[:32, :32] = (80, 120, 160)
    return tile


def test_all_patterns_produce_square_canvases():
    patterns = TilePatterns(default_canvas=512)
    for name in PATTERNS:
        canvas = patterns.create(_tile(), name)
        assert canvas.shape[0] == canvas.shape[1]
        assert canvas.shape[2] == 3
        assert canvas.dtype == np.uint8
        assert canvas.shape[0] >= 512


def test_patterns_are_distinct():
    patterns = TilePatterns(default_canvas=512)
    tile = _tile()
    canvases = {name: patterns.create(tile, name) for name in PATTERNS}

    # Any two patterns must differ in at least some pixels.
    for i, a in enumerate(PATTERNS):
        for b in PATTERNS[i + 1 :]:
            assert np.any(canvases[a] != canvases[b]), f"{a} == {b}"


def test_default_pattern_is_straight():
    tile = _tile()
    patterns = TilePatterns(default_canvas=512)
    np.testing.assert_array_equal(
        patterns.create(tile, "SomethingElse"),
        patterns.create_straight_canvas(tile),
    )
