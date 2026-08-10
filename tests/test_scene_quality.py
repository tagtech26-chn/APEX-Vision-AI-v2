import cv2
import numpy as np

from app.ai.quality import SceneQualityEvaluator
from app.ai.scene.result import SceneResult


def _scene() -> SceneResult:
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[30:90, 10:90] = 255
    depth = np.ones((100, 100), dtype=np.float32)
    polygon = np.array([[10, 30], [90, 30], [90, 90], [10, 90]], dtype=np.float32)
    scene = SceneResult(
        image=image,
        width=100,
        height=100,
        floor_mask=mask,
        depth_map=depth,
        floor_polygon=polygon,
        homography=np.eye(3, dtype=np.float32),
    )
    return scene


def test_scene_quality_returns_high_score_for_valid_geometry() -> None:
    quality = SceneQualityEvaluator().evaluate(_scene())

    assert quality["score"] >= 90
    assert quality["grade"] == "excellent"
    assert quality["floor_coverage"] == 0.48
    assert quality["depth_valid_ratio"] == 1.0
    assert quality["polygon_valid"] is True
    assert quality["homography_valid"] is True


def test_scene_quality_rejects_missing_geometry() -> None:
    scene = _scene()
    scene.floor_polygon = None
    scene.homography = None

    quality = SceneQualityEvaluator().evaluate(scene)

    assert quality["polygon_valid"] is False
    assert quality["homography_valid"] is False
    assert quality["score"] < 90


def test_scene_quality_handles_invalid_scene() -> None:
    scene = SceneResult()

    quality = SceneQualityEvaluator().evaluate(scene)

    assert quality == {
        "score": 0.0,
        "grade": "invalid",
        "floor_coverage": 0.0,
        "depth_valid_ratio": 0.0,
        "polygon_valid": False,
        "homography_valid": False,
    }
