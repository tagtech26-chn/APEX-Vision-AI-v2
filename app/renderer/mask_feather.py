"""Boundary-safe mask feathering for smooth compositing edges."""

from __future__ import annotations

import cv2
import numpy as np


class MaskFeather:
    """Create a soft alpha channel without bleeding outside the source mask."""

    def feather(self, mask: np.ndarray, radius: int = 31) -> np.ndarray:
        """Feather only inside the mask boundary.

        Gaussian blur spreads non-zero alpha outside a binary floor mask. That
        can place a faint amount of the projected material onto walls,
        furniture edges, or other non-floor pixels. A distance transform keeps
        the feather entirely inside the supplied mask while retaining a smooth
        transition at the boundary.
        """
        if mask.ndim == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

        binary = (mask > 0).astype(np.uint8)
        if not np.any(binary):
            return np.zeros(mask.shape[:2], dtype=np.float32)

        radius = max(0, int(radius))
        if radius == 0:
            return binary.astype(np.float32)

        distance = cv2.distanceTransform(binary, cv2.DIST_L2, 3)
        alpha = np.minimum(distance / float(radius), 1.0)
        alpha[binary == 0] = 0.0
        return alpha.astype(np.float32)
