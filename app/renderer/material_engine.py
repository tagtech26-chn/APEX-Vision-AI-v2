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

FINISH_PROFILES: dict[str, dict[str, float]] = {
    "matte": {"contrast": 0.94, "highlight": 0.00},
    "satin": {"contrast": 1.00, "highlight": 0.015},
    "gloss": {"contrast": 1.04, "highlight": 0.035},
}


class MaterialEngine:
    """Enhance a projected material using surface and finish profiles."""

    def enhance(
        self,
        projection: np.ndarray,
        profile: str = "generic",
        finish: str = "satin",
        texture_scale_factor: float = 1.0,
    ) -> np.ndarray:
        params = MATERIAL_PROFILES.get(profile, MATERIAL_PROFILES["generic"])
        finish_params = FINISH_PROFILES.get(finish, FINISH_PROFILES["satin"])
        img = projection.astype(np.float32)

        img *= params["gain"]
        img = np.power(np.clip(img / 255.0, 0, 1), params["gamma"]) * 255.0

        sharp = params["sharp"] * float(np.clip(texture_scale_factor, 1.0, 2.0))
        if sharp > 0:
            blurred = cv2.GaussianBlur(img, (0, 0), 2)
            img = cv2.addWeighted(img, 1.0 + sharp, blurred, -sharp, 0)

        mean = cv2.GaussianBlur(img, (0, 0), 3)
        img = mean + (img - mean) * finish_params["contrast"]
        if finish_params["highlight"] > 0:
            highlights = np.clip((img - 215.0) / 40.0, 0.0, 1.0)
            img += highlights * (255.0 - img) * finish_params["highlight"]

        return np.clip(img, 0, 255).astype(np.uint8)
