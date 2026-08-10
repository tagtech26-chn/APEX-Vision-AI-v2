import numpy as np

from app.ai.scene.geometry_quality import evaluate_floor_geometry


def test_valid_floor_geometry_produces_strong_regression_signal() -> None:
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[25:, :] = 255
    polygon = np.array([[0, 25], [99, 25], [99, 99], [0, 99]], dtype=np.float32)
    homography = np.eye(3, dtype=np.float64)

    quality = evaluate_floor_geometry(mask, polygon, homography)

    assert 0.74 < quality.floor_coverage < 0.76
    assert quality.polygon_area_ratio > 0.70
    assert quality.polygon_convexity == 1.0
    assert quality.homography_valid is True
    assert quality.perspective_score > 0.9
    assert quality.score > 0.8


def test_missing_geometry_is_safe_and_scores_zero() -> None:
    quality = evaluate_floor_geometry(None, None, None)

    assert quality.as_dict() == {
        "floor_coverage": 0.0,
        "polygon_area_ratio": 0.0,
        "polygon_convexity": 0.0,
        "homography_valid": False,
        "perspective_score": 0.0,
        "score": 0.0,
    }


def test_singular_homography_is_rejected() -> None:
    mask = np.ones((10, 10), dtype=np.uint8)
    polygon = np.array([[0, 0], [9, 0], [9, 9], [0, 9]], dtype=np.float32)
    singular = np.zeros((3, 3), dtype=np.float64)

    quality = evaluate_floor_geometry(mask, polygon, singular)

    assert quality.homography_valid is False
    assert quality.perspective_score < 0.6
