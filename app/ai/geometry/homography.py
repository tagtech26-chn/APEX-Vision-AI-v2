"""Homography computation between a floor quad and a top-down plane."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.ai.geometry.polygon import PolygonEngine


@dataclass(slots=True)
class HomographyResult:
    matrix: np.ndarray
    inverse: np.ndarray
    source: np.ndarray
    destination: np.ndarray
    width: int
    height: int


class HomographyEngine:
    """Maps a (4, 2) floor quad to a square top-down plane."""

    def __init__(self, output_width: int = 2048, output_height: int = 2048) -> None:
        self.output_width = output_width
        self.output_height = output_height

    def compute(self, floor_polygon: np.ndarray) -> HomographyResult:
        src = PolygonEngine.order_points(floor_polygon)
        dst = np.array(
            [
                [0, 0],
                [self.output_width - 1, 0],
                [self.output_width - 1, self.output_height - 1],
                [0, self.output_height - 1],
            ],
            dtype=np.float32,
        )

        matrix = cv2.getPerspectiveTransform(src, dst)
        return HomographyResult(
            matrix=matrix,
            inverse=np.linalg.inv(matrix),
            source=src,
            destination=dst,
            width=self.output_width,
            height=self.output_height,
        )
