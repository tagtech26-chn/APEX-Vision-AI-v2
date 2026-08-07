"""Material engine: contrast / gamma / sharpening enhancement."""

from __future__ import annotations

import cv2
import numpy as np


class MaterialEngine:
    """Enhances the tile material before compositing."""

    def enhance(self, projection: np.ndarray) -> np.ndarray:
        img = projection.astype(np.float32)

        img *= 1.03
        img = np.power(np.clip(img / 255.0, 0, 1), 0.95) * 255.0

        blurred = cv2.GaussianBlur(img, (0, 0), 2)
        img = cv2.addWeighted(img, 1.35, blurred, -0.35, 0)

        return np.clip(img, 0, 255).astype(np.uint8)
