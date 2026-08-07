"""Lightweight heuristic object detector (no external models)."""

from __future__ import annotations

import cv2
import numpy as np

from app.ai.detection.base import Detection, ObjectDetector
from app.ai.segmentation.heuristic import estimate_floor_mask


class HeuristicDetector(ObjectDetector):
    """Detects the floor by colour + position heuristics."""

    name = "heuristic"

    def detect(self, image: np.ndarray, prompt: str) -> list[Detection]:
        if prompt != "floor":
            return []

        mask = estimate_floor_mask(image)

        ys, xs = np.where(mask > 0)
        if len(xs) == 0:
            return []

        x1, x2 = int(xs.min()), int(xs.max())
        y1, y2 = int(ys.min()), int(ys.max())

        score = float(mask[y1:y2, x1:x2].mean() / 255.0)
        return [Detection(label="floor", score=score, box=(x1, y1, x2, y2))]
