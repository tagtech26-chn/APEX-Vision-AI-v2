"""Tile projection onto the room floor plane."""

from __future__ import annotations

import cv2
import numpy as np

from app.renderer.grout_engine import GroutEngine
from app.renderer.mask_feather import MaskFeather
from app.renderer.patterns import TilePatterns


class TileProjector:
    """Wraps a patterned canvas into the room perspective."""

    def __init__(self, debug: bool = False) -> None:
        self.patterns = TilePatterns()
        self.grout = GroutEngine()
        self.feather = MaskFeather()
        self.debug = debug

    @staticmethod
    def _to_square(tile: np.ndarray) -> np.ndarray:
        """Center-crop a texture swatch to a square so it isn't stretched.

        Catalog textures are rectangles (2:1, 1.5:1); resizing them straight
        to a square distorts the pattern. Crop the largest centered square.
        """
        h, w = tile.shape[:2]
        if h == w:
            return tile
        side = min(h, w)
        y0 = (h - side) // 2
        x0 = (w - side) // 2
        return tile[y0 : y0 + side, x0 : x0 + side]

    def _tile_pixels(self, tile_size_mm: int) -> int:
        """Projected tile size in canvas pixels.

        The homography plane is a fixed 2048px square representing the whole
        floor quad, so the number of tiles across the floor must be derived
        from that span (not image width). Sizes are kept strictly
        proportional to the tile edge: 600mm ~ 13 tiles, 300mm ~ 26,
        1200mm ~ 6 across a ~7m floor.
        """
        plane_span = 2048
        size = max(100, int(tile_size_mm))
        tiles_across = int(round(7800.0 / size))
        tiles_across = max(3, min(tiles_across, 40))
        return max(48, plane_span // tiles_across)

    @staticmethod
    def _plane_shift(
        homography: np.ndarray,
        floor_mask: np.ndarray,
        canvas_size: int,
    ) -> tuple[float, float]:
        """Shift (px) to centre the floor mask in the pattern canvas.

        Applies the homography to every floor pixel and returns the shift
        needed to place the mask's plane-space bounding box in the middle of
        the canvas. Falls back to (0, 0) when the mask is empty or the box
        cannot fit.
        """
        rows, cols = np.where(floor_mask > 0)
        if rows.size == 0:
            return 0.0, 0.0

        points = np.stack(
            [cols, rows, np.ones_like(cols, dtype=np.float64)], axis=-1
        )
        plane = points @ homography.T
        px = plane[:, 0] / plane[:, 2]
        py = plane[:, 1] / plane[:, 2]

        cx = 0.5 * (float(px.min()) + float(px.max()))
        cy = 0.5 * (float(py.min()) + float(py.max()))
        sx = canvas_size / 2.0 - cx
        sy = canvas_size / 2.0 - cy

        span_x = float(px.max()) - float(px.min())
        span_y = float(py.max()) - float(py.min())
        if span_x > canvas_size or span_y > canvas_size:
            return 0.0, 0.0
        return sx, sy

    def project(
        self,
        tile_image: np.ndarray,
        homography: np.ndarray,
        output_size: tuple[int, int],
        tile_size_mm: int = 600,
        pattern: str = "Straight",
        floor_mask: np.ndarray | None = None,
        grout_width: int = 2,
        grout_color=(220, 220, 220),
    ) -> np.ndarray:
        if homography is None:
            raise RuntimeError("Homography missing.")

        width, height = output_size
        tile_pixels = self._tile_pixels(tile_size_mm)

        # Center-crop the swatch to a square, resize to the projected tile
        # size, and apply grout AFTER resizing so the lines stay visible at
        # the rendered scale instead of being scaled into invisibility.
        tile = self._to_square(tile_image)
        tile = cv2.resize(
            tile,
            (tile_pixels, tile_pixels),
            interpolation=cv2.INTER_CUBIC,
        )
        tile = self.grout.apply(
            tile=tile,
            grout_width_mm=grout_width,
            grout_color=grout_color,
        )

        canvas = self.patterns.create(tile, pattern)

        try:
            transform = np.linalg.inv(homography)
        except np.linalg.LinAlgError:
            transform = homography

        # Floor pixels can map to plane coords outside the quad's [0, 2048]
        # square (e.g. shadowed floor beside a table). warpPerspective paints
        # those black, so shift the sampling so the whole floor mask lands
        # inside the pattern canvas.
        if floor_mask is not None:
            sx, sy = self._plane_shift(homography, floor_mask, canvas.shape[0])
            if sx or sy:
                shift = np.array(
                    [[1, 0, -sx], [0, 1, -sy], [0, 0, 1]], dtype=np.float64
                )
                transform = transform @ shift

        warped = cv2.warpPerspective(
            canvas,
            transform,
            (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0),
        )

        if self.debug:
            cv2.imwrite("output/debug_tile.png", tile)
            cv2.imwrite("output/debug_canvas.png", canvas)
            cv2.imwrite("output/debug_projection.png", warped)

        return warped

    def blend(
        self,
        room: np.ndarray,
        projection: np.ndarray,
        floor_mask: np.ndarray,
        alpha: float = 0.92,
    ) -> np.ndarray:
        mask = self.feather.feather(floor_mask, radius=31)
        mask = mask[..., None]

        room = room.astype(np.float32)
        projection = projection.astype(np.float32)

        # Blend the projection slightly with the original floor so seams vanish.
        projection = projection * alpha + room * (1.0 - alpha)

        result = room * (1.0 - mask) + projection * mask
        result = np.clip(result, 0, 255)

        if self.debug:
            cv2.imwrite("output/debug_final.png", result.astype(np.uint8))

        return result.astype(np.uint8)
