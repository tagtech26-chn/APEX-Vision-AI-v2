"""Tests for the polygon engine."""

from __future__ import annotations

import cv2
import numpy as np

from app.ai.geometry.polygon import PolygonEngine


def _mask_with_quad() -> np.ndarray:
    mask = np.zeros((400, 500), dtype=np.uint8)
    pts = np.array([[120, 120], [380, 120], [380, 380], [120, 380]], dtype=np.int32)
    cv2.fillConvexPoly(mask, pts, 255)
    return mask


def test_extract_returns_ordered_quad():
    polygon = PolygonEngine().extract(_mask_with_quad())
    assert polygon.shape == (4, 2)
    assert polygon.dtype == np.float32

    tl, tr, br, bl = polygon
    assert tl[0] < tr[0]
    assert bl[1] > tl[1]
    assert br[0] > bl[0]


def test_order_points_shuffled():
    pts = np.array([[1, 1], [9, 9], [9, 1], [1, 9]], dtype=np.float32)
    ordered = PolygonEngine.order_points(pts)
    np.testing.assert_allclose(ordered[0], [1, 1])  # TL
    np.testing.assert_allclose(ordered[1], [9, 1])  # TR
    np.testing.assert_allclose(ordered[2], [9, 9])  # BR
    np.testing.assert_allclose(ordered[3], [1, 9])  # BL


def test_extract_raises_on_empty_mask():
    empty = np.zeros((100, 100), dtype=np.uint8)
    try:
        PolygonEngine().extract(empty)
        raised = False
    except RuntimeError:
        raised = True
    assert raised


def test_draw_polygon():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    polygon = np.array([[10, 10], [90, 10], [90, 90], [10, 90]], dtype=np.float32)
    output = PolygonEngine.draw(image, polygon)
    assert output.shape == image.shape


def test_extract_preserves_trapezoid_perspective():
    mask = np.zeros((400, 500), dtype=np.uint8)
    pts = np.array([[200, 120], [300, 120], [480, 380], [20, 380]], dtype=np.int32)
    cv2.fillConvexPoly(mask, pts, 255)

    polygon = PolygonEngine().extract(mask)
    assert polygon.shape == (4, 2)

    tl, tr, br, bl = polygon
    top_width = abs(float(tr[0]) - float(tl[0]))
    bottom_width = abs(float(br[0]) - float(bl[0]))
    assert bottom_width > top_width * 1.5


def test_order_points_handles_perspective_trapezoid():
    # A trapezoid whose TR is not the axis-aligned max(x - y) point.
    pts = np.array(
        [[343, 541], [937, 532], [1412, 966], [0, 969]], dtype=np.float32
    )
    ordered = PolygonEngine.order_points(pts)
    np.testing.assert_allclose(ordered[0], [343, 541])  # TL
    np.testing.assert_allclose(ordered[1], [937, 532])  # TR
    np.testing.assert_allclose(ordered[2], [1412, 966])  # BR
    np.testing.assert_allclose(ordered[3], [0, 969])  # BL
