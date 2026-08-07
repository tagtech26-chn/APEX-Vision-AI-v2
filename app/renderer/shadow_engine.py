"""Shadow engine: preserve existing shadows on the floor."""

from __future__ import annotations

import cv2
import numpy as np


class ShadowEngine:
    """Extracts low-frequency shadows and re-applies them to the projection.

    The shadow map is normalised to its own mean so it adds *relative*
    shading rather than darkening the whole projection.
    """

    def extract(self, room: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(room, cv2.COLOR_BGR2GRAY)
        illumination = cv2.GaussianBlur(gray, (0, 0), sigmaX=55)
        return illumination.astype(np.float32)

    def apply(self, projection: np.ndarray, shadow_mask: np.ndarray) -> np.ndarray:
        mean = float(shadow_mask.mean()) + 1e-6
        factor = np.clip(shadow_mask / mean, 0.75, 1.3)
        result = projection.astype(np.float32)
        result *= factor[..., None]
        return np.clip(result, 0, 255).astype(np.uint8)
