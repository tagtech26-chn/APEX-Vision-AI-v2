"""Lighting engine: extract and apply room illumination."""

from __future__ import annotations

import cv2
import numpy as np


class LightingEngine:
    """Preserves the room's low-frequency lighting on the projection.

    The lighting map is normalised to the *floor's* mean so it acts as
    relative shading (bright areas stay brighter, dark areas stay darker)
    without crushing the projection. The factor range is kept gentle: a tile
    should read as clean and even in every room, not muddy or blown out in
    rooms with strong illumination gradients (bathrooms, kitchens).
    """

    def extract(
        self,
        room: np.ndarray,
        floor_mask: np.ndarray | None = None,
    ) -> np.ndarray:
        gray = cv2.cvtColor(room, cv2.COLOR_BGR2GRAY).astype(np.float32)
        sigma = max(room.shape[:2]) / 35.0
        return cv2.GaussianBlur(gray, (0, 0), sigma)

    def apply(
        self,
        projection: np.ndarray,
        lighting: np.ndarray,
        floor_mask: np.ndarray | None = None,
    ) -> np.ndarray:
        if floor_mask is not None and np.any(floor_mask > 0):
            ref = lighting[floor_mask > 0]
        else:
            ref = lighting
        mean = float(ref.mean()) + 1e-6
        factor = np.clip(lighting / mean, 0.82, 1.22)
        result = projection.astype(np.float32)
        result *= factor[..., None]
        return np.clip(result, 0, 255).astype(np.uint8)
