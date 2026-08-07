"""Lightweight heuristic depth estimator (no external models).

Produces a plausible gradient-based depth map where the bottom of the
frame (closer to the camera) is "near" and the top is "far".
"""

from __future__ import annotations

import cv2
import numpy as np

from app.ai.depth.base import DepthEstimator


class HeuristicDepth(DepthEstimator):
    """Gradient depth prior used when no depth model is available."""

    name = "heuristic"

    def predict(self, image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]

        # Vertical gradient: 0 at top (far) -> 1 at bottom (near).
        yy = np.linspace(0.0, 1.0, h, dtype=np.float32)
        depth = np.tile(yy[:, None], (1, w))

        # Fade the sides slightly for a more natural perspective.
        x_weights = np.linspace(0.85, 1.15, w, dtype=np.float32)
        depth *= x_weights[None, :]
        depth = np.clip(depth, 0.0, 1.0)

        # Smooth a little.
        depth = cv2.GaussianBlur(depth, (0, 0), 2)

        # Ignore non-floor regions by re-normalising to the floor mask later.
        return self.normalise(depth)
