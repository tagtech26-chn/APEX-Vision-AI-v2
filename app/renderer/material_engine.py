"""Material-aware enhancement for projected surface textures."""

from __future__ import annotations

import cv2
import numpy as np


MATERIAL_PROFILES: dict[str, dict[str, float]] = {
    "generic": {"gain": 1.03, "gamma": 0.95, "sharp": 0.35},
    "ceramic": {"gain": 1.03, "gamma": 0.95, "sharp": 0.35},
    "stone": {"gain": 1.01, "gamma": 0.97, "sharp": 0.20},
    "wood": {"gain": 1.00, "gamma": 1.02, "sharp": 0.12},
    "vinyl": {"gain": 1.01, "gamma": 1.00, "sharp": 0.16},
    "carpet": {"gain": 0.99, "gamma": 1.04, "sharp": 0.04},
}


class MaterialEngine:
    """Enhance a projected material using a deterministic surface profile."""

    def enhance(self, projection: np.ndarray, profile: str = "generic") -> np.ndarray:
        params = MATERIAL_PROFILES.get(profile, MATERIAL_PROFILES["generic"])
        img = projection.astype(np.float32)

        img *= params["gain"]
        img = np.power(np.clip(img / 255.0, 0, 1), params["gamma"]) * 255.0

        sharp = params["sharp"]
        if sharp > 0:
            blurred = cv2.GaussianBlur(img, (0, 0), 2)
            img = cv2.addWeighted(img, 1.0 + sharp, blurred, -sharp, 0)

        return np.clip(img, 0, 255).astype(np.uint8)
