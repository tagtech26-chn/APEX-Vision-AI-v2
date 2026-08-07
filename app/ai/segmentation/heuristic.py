"""Lightweight heuristic floor segmenter (no external models)."""

from __future__ import annotations

import cv2
import numpy as np

from app.ai.segmentation.base import SamplerSegmenterMixin, Segmenter


def estimate_floor_mask(image: np.ndarray) -> np.ndarray:
    """Automatically estimate the visible floor mask.

    Uses adaptive LAB colour distance from a bottom-centre seed band, then
    carves out high-texture regions (rugs, patterned furniture) that the
    colour threshold cannot separate from the floor.
    """
    h, w = image.shape[:2]

    y0 = int(h * 0.94)
    x0, x1 = int(w * 0.20), int(w * 0.80)
    if y0 >= h or x0 >= x1:
        return np.zeros((h, w), dtype=np.uint8)

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
    seed = lab[y0:, x0:x1]
    seed_median = np.median(seed.reshape(-1, 3), axis=0)

    dist = np.abs(lab - seed_median).sum(axis=2)
    region = dist[y0:, x0:x1]
    threshold = float(np.maximum(region.mean() + 2.5 * region.std(), 12.0))

    mask = (dist < threshold).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = _largest_component(mask)

    mask = _carve_high_texture(mask, image)

    # One larger opening trims thin colour-bridged bands above the true floor
    # horizon (they connect to the floor but do not belong to it).
    fine = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, fine, iterations=1)

    return mask.astype(np.uint8)


def _carve_high_texture(mask: np.ndarray, image: np.ndarray) -> np.ndarray:
    """Remove rugs/furniture inside the floor that are textured differently."""
    if (mask > 0).sum() == 0:
        return mask

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray2 = cv2.boxFilter(gray * gray, -1, (15, 15))
    mean = cv2.boxFilter(gray, -1, (15, 15))
    local_std = np.sqrt(np.maximum(gray2 - mean * mean, 0.0))

    # Smooth floors stay well below the rug's texture; a textured floor raises
    # the threshold via its own median so it is never stripped.
    floor_median = float(np.median(local_std[mask > 0]))
    carve_threshold = max(14.0, floor_median * 5.0)

    # Only carve interior pixels: the mask boundary has a high local std band
    # (wall/floor edge) that must be kept so the floor isn't stripped.
    interior = cv2.erode(mask, np.ones((15, 15), np.uint8))

    carved = mask.copy()
    carved[(local_std > carve_threshold) & (interior > 0)] = 0
    return _largest_component(carved)


def _largest_component(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if count <= 1:
        return mask

    largest = 1
    largest_area = stats[1, cv2.CC_STAT_AREA]
    for i in range(2, count):
        area = stats[i, cv2.CC_STAT_AREA]
        if area > largest_area:
            largest = i
            largest_area = area

    result = np.zeros(mask.shape, dtype=np.uint8)
    result[labels == largest] = 255
    return result


class HeuristicSegmenter(SamplerSegmenterMixin, Segmenter):
    """Produces a floor mask via adaptive LAB colour + texture heuristics."""

    name = "heuristic"

    def segment(
        self,
        image: np.ndarray,
        box: tuple[int, int, int, int] | None = None,
        points: np.ndarray | None = None,
    ) -> np.ndarray:
        return estimate_floor_mask(image)
