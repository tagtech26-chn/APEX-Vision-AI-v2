"""Mask feathering for smooth compositing edges."""

from __future__ import annotations

import cv2
import numpy as np


class MaskFeather:
    """Softens a binary mask into a smooth 0..1 alpha channel."""

    def feather(self, mask: np.ndarray, radius: int = 31) -> np.ndarray:
        if mask.ndim == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

        if radius > 1:
            mask = cv2.GaussianBlur(mask, (radius, radius), 0)

        return mask.astype(np.float32) / 255.0
