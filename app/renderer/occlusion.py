"""Occlusion handling for protected foreground objects during material compositing."""

from __future__ import annotations

import numpy as np


class OcclusionMask:
    """Keeps projected material behind detected foreground objects."""

    @staticmethod
    def apply(alpha: np.ndarray, protected_mask: np.ndarray | None) -> np.ndarray:
        """Remove material alpha wherever a protected object is present.

        ``protected_mask`` is a binary or grayscale segmentation mask where
        non-zero pixels belong to furniture, rugs, fixtures, people, or other
        foreground objects that must remain visible above the floor material.
        The operation never creates alpha outside the existing floor alpha.
        """
        if protected_mask is None:
            return alpha.astype(np.float32, copy=True)

        if alpha.ndim != 2:
            raise ValueError("alpha must be a 2D array")
        if protected_mask.shape[:2] != alpha.shape:
            raise ValueError("protected_mask must match alpha dimensions")

        protected = protected_mask > 0
        result = alpha.astype(np.float32, copy=True)
        result[protected] = 0.0
        return result
