"""Object detection abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class Detection:
    label: str
    score: float
    box: tuple[int, int, int, int]  # x1, y1, x2, y2


class ObjectDetector(ABC):
    """Detects regions of interest (e.g. the floor) in an image."""

    name: str = "base"

    @abstractmethod
    def detect(self, image: np.ndarray, prompt: str) -> list[Detection]:
        """Return detections for a prompt."""

    def detect_floor(self, image: np.ndarray) -> Detection:
        detections = self.detect(image, "floor")
        if not detections:
            raise RuntimeError("Floor not detected.")
        return max(detections, key=lambda d: d.score)
