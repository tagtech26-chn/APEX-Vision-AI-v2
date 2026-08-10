"""Main tile renderer orchestrator."""

from __future__ import annotations

import cv2
import numpy as np

from app.ai.scene.result import SceneResult
from app.renderer.color_matcher import ColorMatcher
from app.renderer.grout_engine import GroutEngine
from app.renderer.lighting_engine import LightingEngine
from app.renderer.material_engine import MaterialEngine
from app.renderer.tile_projector import TileProjector


class TileRenderer:
    """Composites a material into a scene using a surface-specific profile."""

    def __init__(self, debug: bool = False) -> None:
        self.projector = TileProjector(debug=debug)
        self.grout = GroutEngine()
        self.matcher = ColorMatcher()
        self.lighting = LightingEngine()
        self.material = MaterialEngine()

    def render(
        self,
        scene: SceneResult,
        tile: np.ndarray,
        alpha: float = 0.92,
        grout_width: int = 2,
        grout_color=(220, 220, 220),
        tile_size_mm: int = 600,
        pattern: str = "Straight",
        material_profile: str = "generic",
        material_intelligence: dict[str, object] | None = None,
    ) -> np.ndarray:
        if scene.image is None:
            raise RuntimeError("Scene image missing.")
        if scene.floor_mask is None:
            raise RuntimeError("Floor mask missing.")
        if scene.homography is None:
            raise RuntimeError("Homography missing.")

        render_mask = self._floor_render_mask(scene)

        projection = self.projector.project(
            tile_image=tile,
            homography=scene.homography,
            output_size=scene.size,
            tile_size_mm=tile_size_mm,
            pattern=pattern,
            floor_mask=render_mask,
            grout_width=grout_width,
            grout_color=grout_color,
        )
        if self.projector.last_scale_diagnostics is not None:
            scene.metadata["projection_scale"] = dict(self.projector.last_scale_diagnostics)

        projection = self.material.enhance(
            projection,
            profile=material_profile,
            finish=str((material_intelligence or {}).get("finish", "satin")),
            texture_scale_factor=float((material_intelligence or {}).get("texture_scale_factor", 1.0)),
        )

        lighting = self.lighting.extract(scene.image, render_mask)
        projection = self.lighting.apply(projection, lighting, render_mask)

        projection = self.matcher.match(
            room=scene.image,
            projection=projection,
            floor_mask=render_mask,
        )

        protected = scene.protected_object_mask
        if protected is not None:
            scene.metadata.setdefault("occlusion", {})["applied"] = True
            scene.metadata["occlusion"]["protected_pixels"] = int((protected > 0).sum())

        return self.projector.blend(
            room=scene.image,
            projection=projection,
            floor_mask=render_mask,
            alpha=alpha,
            occlusion_mask=protected,
        )

    @staticmethod
    def _floor_render_mask(scene: SceneResult) -> np.ndarray:
        """Mask covering the visible floor to tile."""
        if scene.floor_mask is None:
            return np.zeros(scene.size[::-1], dtype=np.uint8)
        return scene.floor_mask
