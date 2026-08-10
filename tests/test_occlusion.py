from __future__ import annotations

import numpy as np
import pytest

from app.renderer.occlusion import OcclusionMask


def test_occlusion_removes_projection_from_protected_object() -> None:
    alpha = np.ones((6, 6), dtype=np.float32)
    protected = np.zeros((6, 6), dtype=np.uint8)
    protected[2:4, 2:4] = 255

    result = OcclusionMask.apply(alpha, protected)

    assert np.all(result[2:4, 2:4] == 0.0)
    assert np.all(result[:2] == 1.0)
    assert np.all(result[4:] == 1.0)
    assert np.all(result[2:4, :2] == 1.0)
    assert np.all(result[2:4, 4:] == 1.0)


def test_occlusion_preserves_existing_floor_alpha() -> None:
    alpha = np.array([[0.0, 0.5, 1.0]], dtype=np.float32)
    protected = np.array([[0, 0, 255]], dtype=np.uint8)

    result = OcclusionMask.apply(alpha, protected)

    np.testing.assert_array_equal(result, [[0.0, 0.5, 0.0]])


def test_occlusion_without_mask_is_noop() -> None:
    alpha = np.array([[0.0, 0.5, 1.0]], dtype=np.float32)

    result = OcclusionMask.apply(alpha, None)

    np.testing.assert_array_equal(result, alpha)


def test_occlusion_rejects_mismatched_dimensions() -> None:
    alpha = np.ones((4, 4), dtype=np.float32)
    protected = np.ones((3, 4), dtype=np.uint8)

    with pytest.raises(ValueError, match="dimensions"):
        OcclusionMask.apply(alpha, protected)


def test_occlusion_leakage_diagnostics_detects_leaked_alpha() -> None:
    alpha = np.ones((4, 4), dtype=np.float32)
    protected = np.zeros((4, 4), dtype=np.uint8)
    protected[1:3, 1:3] = 255
    alpha[1, 1] = 0.25

    result = OcclusionMask.leakage_diagnostics(alpha, protected)

    assert result == {
        "protected_pixels": 4,
        "leaked_pixels": 1,
        "leakage_ratio": 0.25,
        "passes": False,
    }


def test_occlusion_leakage_diagnostics_passes_after_carve() -> None:
    alpha = np.ones((4, 4), dtype=np.float32)
    protected = np.zeros((4, 4), dtype=np.uint8)
    protected[1:3, 1:3] = 255

    carved = OcclusionMask.apply(alpha, protected)
    result = OcclusionMask.leakage_diagnostics(carved, protected)

    assert result == {
        "protected_pixels": 4,
        "leaked_pixels": 0,
        "leakage_ratio": 0.0,
        "passes": True,
    }


def test_occlusion_leakage_diagnostics_without_mask_is_zero() -> None:
    alpha = np.ones((2, 2), dtype=np.float32)

    result = OcclusionMask.leakage_diagnostics(alpha, None)

    assert result == {
        "protected_pixels": 0,
        "leaked_pixels": 0,
        "leakage_ratio": 0.0,
        "passes": True,
    }
