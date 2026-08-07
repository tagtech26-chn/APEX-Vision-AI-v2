"""Segmentation abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from app.ai.detection.base import Detection


class Segmenter(ABC):
    """Produces a binary mask from an image and an optional box."""

    name: str = "base"

    @abstractmethod
    def segment(
        self,
        image: np.ndarray,
        box: tuple[int, int, int, int] | None = None,
        points: np.ndarray | None = None,
    ) -> np.ndarray:
        """Return a binary mask (uint8, 0/255)."""


class SamplerSegmenterMixin:
    """Shared helper for heuristic segmenters."""

    @staticmethod
    def to_binary(mask: np.ndarray, threshold: int = 127) -> np.ndarray:
        import cv2

        _, binary = cv2.threshold(mask, threshold, 255, cv2.THRESH_BINARY)
        return binary.astype(np.uint8)

    @staticmethod
    def _box_mask(shape, box, margin: float = 0.0):
        import numpy as np

        h, w = shape[:2]
        x1, y1, x2, y2 = box
        if margin > 0:
            dx = (x2 - x1) * margin
            dy = (y2 - y1) * margin
            x1 = max(0, int(x1 - dx))
            y1 = max(0, int(y1 - dy))
            x2 = min(w - 1, int(x2 + dx))
            y2 = min(h - 1, int(y2 + dy))
        mask = np.zeros((h, w), dtype=np.uint8)
        mask[y1:y2, x1:x2] = 255
        return mask
