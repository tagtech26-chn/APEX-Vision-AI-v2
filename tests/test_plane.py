"""Tests for the plane estimator."""

from __future__ import annotations

import numpy as np

from app.ai.geometry.plane import PlaneEstimator


def test_estimate_on_flat_plane():
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[20:80, 20:80] = 255

    # Constant depth => horizontal plane, pitch/roll near 0.
    depth = np.full((100, 100), 0.5, dtype=np.float32)
    result = PlaneEstimator().estimate(mask, depth)

    assert result.equation.shape == (4,)
    assert abs(result.pitch) < 1e-3
    assert abs(result.roll) < 1e-3
    # Normal points straight up (mostly z).
    assert abs(result.normal[2]) > 0.99


def test_estimate_requires_pixels():
    mask = np.zeros((50, 50), dtype=np.uint8)
    depth = np.zeros((50, 50), dtype=np.float32)

    try:
        PlaneEstimator().estimate(mask, depth)
        raised = False
    except ValueError:
        raised = True
    assert raised
