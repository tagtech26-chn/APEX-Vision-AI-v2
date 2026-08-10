"""Geometry quality metrics for floor-plane and perspective regression checks."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True, slots=True)
class GeometryQuality:
    """Deterministic, model-agnostic quality measurements for a scene floor."""

    floor_coverage: float
    polygon_area_ratio: float
    polygon_convexity: float
    homography_valid: bool
    perspective_score: float
    score: float

    def as_dict(self) -> dict[str, object]:
        return {
            "floor_coverage": self.floor_coverage,
            "polygon_area_ratio": self.polygon_area_ratio,
            "polygon_convexity": self.polygon_convexity,
            "homography_valid": self.homography_valid,
            "perspective_score": self.perspective_score,
            "score": self.score,
        }

    def passes_regression_gate(
        self,
        *,
        min_score: float = 0.60,
        min_floor_coverage: float = 0.05,
    ) -> bool:
        """Return whether geometry is strong enough for a regression fixture.

        This is deliberately a regression gate, not a claim of semantic accuracy.
        Real-world quality thresholds must be calibrated against labelled data.
        """
        return (
            0.0 <= min_score <= 1.0
            and 0.0 <= min_floor_coverage <= 1.0
            and self.floor_coverage >= min_floor_coverage
            and self.homography_valid
            and self.score >= min_score
        )


def evaluate_floor_geometry(
    floor_mask: np.ndarray | None,
    floor_polygon: np.ndarray | None,
    homography: np.ndarray | None,
) -> GeometryQuality:
    """Measure floor coverage, polygon validity and homography plausibility.

    These metrics intentionally do not claim semantic correctness. They provide
    stable signals for regression tests and future labelled-image evaluation.
    """
    if floor_mask is None or floor_mask.size == 0:
        return GeometryQuality(0.0, 0.0, 0.0, False, 0.0, 0.0)

    mask = np.asarray(floor_mask)
    coverage = float(np.count_nonzero(mask) / mask.size)

    polygon_ratio = 0.0
    convexity = 0.0
    if floor_polygon is not None:
        points = np.asarray(floor_polygon, dtype=np.float32).reshape(-1, 2)
        if len(points) >= 3:
            image_area = float(mask.shape[0] * mask.shape[1])
            area = abs(float(cv2.contourArea(points)))
            polygon_ratio = area / image_area if image_area else 0.0
            hull = cv2.convexHull(points)
            hull_area = abs(float(cv2.contourArea(hull)))
            convexity = min(1.0, area / hull_area) if hull_area > 0 else 0.0

    homography_valid = False
    if homography is not None:
        matrix = np.asarray(homography, dtype=np.float64)
        if matrix.shape == (3, 3) and np.all(np.isfinite(matrix)):
            determinant = float(np.linalg.det(matrix))
            homography_valid = abs(determinant) > 1e-10

    coverage_score = min(1.0, coverage / 0.75)
    polygon_score = min(1.0, polygon_ratio / 0.75) if polygon_ratio else 0.0
    perspective_score = (
        (0.5 * float(homography_valid))
        + (0.3 * convexity)
        + (0.2 * polygon_score)
    )
    score = (
        0.35 * coverage_score
        + 0.25 * polygon_score
        + 0.20 * convexity
        + 0.20 * perspective_score
    )

    return GeometryQuality(
        floor_coverage=coverage,
        polygon_area_ratio=polygon_ratio,
        polygon_convexity=convexity,
        homography_valid=homography_valid,
        perspective_score=perspective_score,
        score=min(1.0, max(0.0, score)),
    )
