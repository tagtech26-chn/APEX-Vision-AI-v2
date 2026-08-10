"""Deterministic surface-material and finish intelligence baseline."""

from __future__ import annotations

import cv2
import numpy as np

MATERIALS = ("ceramic", "stone", "wood", "vinyl", "carpet")
FINISHES = ("matte", "satin", "gloss")


def classify_surface(image: np.ndarray) -> dict[str, object]:
    """Estimate material, finish and texture scale from measurable statistics.

    This is a deterministic baseline, not a learned AI model. It provides
    stable material intelligence until a labelled dataset is available for a
    trained classifier.
    """
    if image is None or image.size == 0:
        raise ValueError("Surface image is empty")
    if image.ndim not in (2, 3):
        raise ValueError("Surface image must be 2D or 3D")

    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = gray.astype(np.uint8, copy=False)
    height, width = gray.shape[:2]
    if min(height, width) < 8:
        raise ValueError("Surface image is too small")

    laplacian = cv2.Laplacian(gray, cv2.CV_32F)
    texture = float(np.var(laplacian))
    edges = cv2.Canny(gray, 80, 160)
    edge_density = float(np.count_nonzero(edges)) / float(edges.size)

    profile = gray.mean(axis=0 if width >= height else 1).astype(np.float32)
    profile -= profile.mean()
    norm = float(np.dot(profile, profile))
    periodicity = 0.0
    if norm > 1e-6 and len(profile) >= 8:
        max_lag = min(len(profile) // 2, 64)
        correlations = [float(np.dot(profile[:-lag], profile[lag:]) / norm) for lag in range(2, max_lag)]
        periodicity = max(0.0, max(correlations, default=0.0))

    gray_float = gray.astype(np.float32)
    local_mean = cv2.GaussianBlur(gray_float, (0, 0), 3)
    highlight_ratio = float(np.mean((gray_float > 235) & (gray_float > local_mean + 18.0)))
    local_contrast = float(np.std(gray_float - local_mean))

    if edge_density < 0.035 and texture < 180:
        material = "carpet"
    elif periodicity > 0.45 and edge_density > 0.06:
        material = "ceramic"
    elif texture > 900 and edge_density > 0.12:
        material = "stone"
    elif edge_density > 0.08 and periodicity < 0.25:
        material = "wood"
    else:
        material = "vinyl"

    if highlight_ratio >= 0.018 and local_contrast >= 7.0:
        finish = "gloss"
    elif highlight_ratio >= 0.006 or local_contrast >= 4.0:
        finish = "satin"
    else:
        finish = "matte"

    confidence = min(
        1.0,
        max(
            0.0,
            0.35
            + min(texture / 3000.0, 0.30)
            + min(edge_density / 0.2, 0.18)
            + periodicity * 0.08
            + min(local_contrast / 40.0, 0.09),
        ),
    )
    texture_frequency = max(0.0, edge_density * 0.5 + periodicity * 0.5)
    scale_factor = float(np.clip(1.0 + texture_frequency * 2.0, 1.0, 2.0))

    return {
        "material": material,
        "finish": finish,
        "confidence": round(confidence, 4),
        "texture_scale_factor": round(scale_factor, 4),
        "features": {
            "texture_variance": round(texture, 4),
            "edge_density": round(edge_density, 6),
            "periodicity": round(periodicity, 6),
            "highlight_ratio": round(highlight_ratio, 6),
            "local_contrast": round(local_contrast, 4),
        },
        "method": "deterministic-baseline-v2",
    }
