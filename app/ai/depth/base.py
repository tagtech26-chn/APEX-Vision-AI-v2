"""Depth estimation abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class DepthEstimator(ABC):
    """Estimates per-pixel depth for an image."""

    name: str = "base"

    @abstractmethod
    def predict(self, image: np.ndarray) -> np.ndarray:
        """Return a normalised float32 depth map in the range 0..1."""

    @staticmethod
    def normalise(depth: np.ndarray) -> np.ndarray:
        d = depth.astype(np.float32)
        d -= d.min()
        if d.max() > 0:
            d /= d.max()
        return d
