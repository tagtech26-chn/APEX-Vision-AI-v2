"""Tests for the homography engine."""

from __future__ import annotations

import numpy as np
import pytest

from app.ai.geometry.homography import HomographyEngine


def test_compute_returns_valid_matrix():
    polygon = np.array(
        [[100, 100], [300, 100], [300, 300], [100, 300]], dtype=np.float32
    )
    engine = HomographyEngine(output_width=2048, output_height=2048)
    result = engine.compute(polygon)

    assert result.matrix.shape == (3, 3)
    assert result.inverse.shape == (3, 3)
    assert result.source.shape == (4, 2)
    assert result.destination.shape == (4, 2)
    assert result.width == 2048
    assert result.height == 2048

    # Forward + inverse round-trips.
    identity = result.matrix @ result.inverse
    np.testing.assert_allclose(identity, np.eye(3), atol=1e-4)


def test_points_are_ordered_tl_tr_br_bl():
    # Deliberately shuffled input.
    polygon = np.array(
        [[300, 300], [100, 100], [100, 300], [300, 100]], dtype=np.float32
    )
    result = HomographyEngine().compute(polygon)

    tl, tr, br, bl = result.source
    assert tl[0] < tr[0]
    assert tr[1] < br[1]
    assert br[0] > bl[0]
    assert bl[1] > tl[1]


def test_compute_requires_four_points():
    with pytest.raises(Exception):
        HomographyEngine().compute(np.zeros((3, 2), dtype=np.float32))
