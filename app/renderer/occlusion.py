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

    @staticmethod
    def leakage_diagnostics(
        alpha: np.ndarray,
        protected_mask: np.ndarray | None,
        threshold: float = 1e-6,
    ) -> dict[str, float | int | bool]:
        """Measure material alpha that remains inside protected objects.

        The diagnostic is deliberately independent from ``apply`` so tests and
        production instrumentation can detect a future compositing regression.
        """
        if alpha.ndim != 2:
            raise ValueError("alpha must be a 2D array")
        if protected_mask is None:
            return {
                "protected_pixels": 0,
                "leaked_pixels": 0,
                "leakage_ratio": 0.0,
                "passes": True,
            }
        if protected_mask.shape[:2] != alpha.shape:
            raise ValueError("protected_mask must match alpha dimensions")
        if threshold < 0:
            raise ValueError("threshold must be non-negative")

        protected = protected_mask > 0
        protected_pixels = int(protected.sum())
        if protected_pixels == 0:
            return {
                "protected_pixels": 0,
                "leaked_pixels": 0,
                "leakage_ratio": 0.0,
                "passes": True,
            }

        leaked = protected & (alpha > threshold)
        leaked_pixels = int(leaked.sum())
        ratio = leaked_pixels / protected_pixels
        return {
            "protected_pixels": protected_pixels,
            "leaked_pixels": leaked_pixels,
            "leakage_ratio": float(ratio),
            "passes": leaked_pixels == 0,
        }
