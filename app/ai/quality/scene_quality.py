"""Deterministic quality signals for AI-generated scene geometry."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.ai.scene.result import SceneResult


@dataclass(frozen=True, slots=True)
class SceneQualityEvaluator:
    """Scores scene-analysis outputs without changing the render result.

    The score is intentionally deterministic and model-agnostic. It provides
    operational quality signals that can be used for regression testing,
    diagnostics, and future provider/model comparison.
    """

    min_floor_coverage: float = 0.02
    max_floor_coverage: float = 0.90
    min_depth_valid_ratio: float = 0.50

    def evaluate(self, scene: SceneResult) -> dict[str, float | str | bool]:
        if scene.image is None or scene.floor_mask is None:
            return {
                "score": 0.0,
                "grade": "invalid",
                "floor_coverage": 0.0,
                "depth_valid_ratio": 0.0,
                "polygon_valid": False,
                "homography_valid": False,
            }

        image_area = float(max(1, scene.width * scene.height))
        floor_pixels = float(np.count_nonzero(scene.floor_mask))
        floor_coverage = floor_pixels / image_area
        coverage_score = self._range_score(
            floor_coverage, self.min_floor_coverage, self.max_floor_coverage
        )

        depth_valid_ratio = 0.0
        if scene.depth_map is not None:
            depth = np.asarray(scene.depth_map)
            finite = np.isfinite(depth)
            positive = depth > 0
            depth_valid_ratio = float(np.count_nonzero(finite & positive)) / float(max(1, depth.size))
        depth_score = self._range_score(depth_valid_ratio, self.min_depth_valid_ratio, 1.0)

        polygon_valid = self._polygon_valid(scene.floor_polygon, scene.floor_mask.shape)
        homography_valid = self._homography_valid(scene.homography)

        geometry_score = (float(polygon_valid) + float(homography_valid)) / 2.0
        score = 100.0 * (
            0.45 * coverage_score
            + 0.25 * depth_score
            + 0.30 * geometry_score
        )

        return {
            "score": round(score, 2),
            "grade": self._grade(score),
            "floor_coverage": round(floor_coverage, 6),
            "depth_valid_ratio": round(depth_valid_ratio, 6),
            "polygon_valid": polygon_valid,
            "homography_valid": homography_valid,
        }

    @staticmethod
    def _range_score(value: float, minimum: float, maximum: float) -> float:
        if value < minimum:
            span = max(minimum, 1e-9)
            return max(0.0, value / span)
        if value > maximum:
            return max(0.0, 1.0 - (value - maximum) / max(1.0 - maximum, 1e-9))
        return 1.0

    @staticmethod
    def _polygon_valid(polygon: np.ndarray | None, shape: tuple[int, int]) -> bool:
        if polygon is None:
            return False
        points = np.asarray(polygon, dtype=np.float32).reshape(-1, 2)
        if len(points) < 4 or not np.isfinite(points).all():
            return False
        height, width = shape
        area = abs(float(cv2.contourArea(points)))
        return area >= 0.005 * width * height

    @staticmethod
    def _homography_valid(matrix: np.ndarray | None) -> bool:
        if matrix is None:
            return False
        h = np.asarray(matrix, dtype=np.float64)
        if h.shape != (3, 3) or not np.isfinite(h).all():
            return False
        determinant = abs(float(np.linalg.det(h)))
        return determinant > 1e-9

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 90:
            return "excellent"
        if score >= 75:
            return "good"
        if score >= 60:
            return "review"
        return "poor"
