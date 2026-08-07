"""Grout painting engine."""

from __future__ import annotations

import cv2
import numpy as np


class GroutEngine:
    """Paints a grout border around the edges of a tile."""

    def __init__(self) -> None:
        # Approximate mm -> pixels at the projected tile scale.
        self.mm_to_pixel = {1: 1, 2: 2, 3: 3, 5: 5}

    def apply(
        self,
        tile: np.ndarray,
        grout_width_mm: int = 2,
        grout_color=(220, 220, 220),
    ) -> np.ndarray:
        result = tile.copy()
        h, w = result.shape[:2]

        thickness = self.mm_to_pixel.get(grout_width_mm, 2)
        color = tuple(int(c) for c in grout_color)

        cv2.rectangle(result, (0, 0), (w, thickness), color, -1)
        cv2.rectangle(result, (0, h - thickness), (w, h), color, -1)
        cv2.rectangle(result, (0, 0), (thickness, h), color, -1)
        cv2.rectangle(result, (w - thickness, 0), (w, h), color, -1)

        return result
