"""Lightweight heuristic object detector (no external models)."""

from __future__ import annotations

import cv2
import numpy as np

from app.ai.detection.base import Detection, ObjectDetector
from app.ai.segmentation.heuristic import estimate_floor_mask


_FURNITURE_TERMS = {
    "sofa",
    "couch",
    "armchair",
    "chair",
    "table",
    "rug",
    "plant",
    "lamp",
    "cabinet",
    "bed",
    "furniture",
    "obstruction",
}


class HeuristicDetector(ObjectDetector):
    """Detect floor and foreground obstructions without external models.

    The light provider has no semantic vision model, so obstruction detection
    is deliberately geometric: first estimate the floor, then look for
    connected non-floor regions inside the visible floor envelope. This keeps
    walls and ceiling out of the candidate set while still detecting furniture
    that the floor segmenter has carved away.
    """

    name = "heuristic"

    def detect(self, image: np.ndarray, prompt: str) -> list[Detection]:
        prompt_normalized = prompt.strip().lower()
        if prompt_normalized == "floor":
            return self._detect_floor(image)

        if not any(term in prompt_normalized for term in _FURNITURE_TERMS):
            return []

        return self._detect_foreground_obstructions(image)

    @staticmethod
    def _detect_floor(image: np.ndarray) -> list[Detection]:
        mask = estimate_floor_mask(image)
        ys, xs = np.where(mask > 0)
        if len(xs) == 0:
            return []

        x1, x2 = int(xs.min()), int(xs.max())
        y1, y2 = int(ys.min()), int(ys.max())
        region = mask[y1:y2, x1:x2]
        score = float(region.mean() / 255.0) if region.size else 0.0
        return [Detection(label="floor", score=score, box=(x1, y1, x2, y2))]

    @staticmethod
    def _detect_foreground_obstructions(image: np.ndarray) -> list[Detection]:
        floor_mask = estimate_floor_mask(image)
        if not np.any(floor_mask):
            return []

        height, width = floor_mask.shape[:2]
        binary_floor = floor_mask > 0

        # Find the upper boundary of the visible floor for each column. Pixels
        # below that boundary can contain furniture; pixels above it are wall,
        # windows, TV, etc. and must not become false obstructions.
        floor_top = np.full(width, height, dtype=np.int32)
        for x in range(width):
            rows = np.flatnonzero(binary_floor[:, x])
            if rows.size:
                floor_top[x] = int(rows[0])

        yy = np.arange(height)[:, None]
        floor_envelope = yy >= floor_top[None, :]
        candidates = floor_envelope & ~binary_floor

        # Suppress tiny segmentation noise and close small gaps in furniture
        # silhouettes before connected-component extraction.
        candidate_mask = candidates.astype(np.uint8) * 255
        candidate_mask = cv2.morphologyEx(
            candidate_mask,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
            iterations=2,
        )
        candidate_mask = cv2.morphologyEx(
            candidate_mask,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
            iterations=1,
        )

        count, labels, stats, _ = cv2.connectedComponentsWithStats(
            candidate_mask,
            connectivity=8,
        )
        image_area = float(height * width)
        min_area = max(64.0, image_area * 0.00025)
        max_area = image_area * 0.65

        detections: list[Detection] = []
        for idx in range(1, count):
            area = float(stats[idx, cv2.CC_STAT_AREA])
            x = int(stats[idx, cv2.CC_STAT_LEFT])
            y = int(stats[idx, cv2.CC_STAT_TOP])
            w = int(stats[idx, cv2.CC_STAT_WIDTH])
            h = int(stats[idx, cv2.CC_STAT_HEIGHT])

            if area < min_area or area > max_area or w < 8 or h < 8:
                continue

            # A component touching almost the entire image width is normally a
            # bad floor-horizon split rather than a foreground object.
            if w >= int(width * 0.92) and h >= int(height * 0.15):
                continue

            box_area = float(max(w * h, 1))
            compactness = min(1.0, area / box_area)
            score = float(np.clip(0.55 + 0.4 * compactness, 0.55, 0.95))
            detections.append(
                Detection(
                    label="furniture",
                    score=score,
                    box=(x, y, x + w, y + h),
                )
            )

        detections.sort(key=lambda detection: detection.score, reverse=True)
        return detections
