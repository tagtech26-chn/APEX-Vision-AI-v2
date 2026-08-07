"""Colour matcher: align projection brightness with the room floor."""

from __future__ import annotations

import cv2
import numpy as np


class ColorMatcher:
    """Matches the projection's LAB brightness to the room's floor."""

    def match(
        self,
        room: np.ndarray,
        projection: np.ndarray,
        floor_mask: np.ndarray,
    ) -> np.ndarray:
        if floor_mask.ndim == 3:
            mask = cv2.cvtColor(floor_mask, cv2.COLOR_BGR2GRAY)
        else:
            mask = floor_mask.copy()

        mask_bool = mask > 0
        if not np.any(mask_bool):
            return projection

        room_lab = cv2.cvtColor(room, cv2.COLOR_BGR2LAB).astype(np.float32)
        proj_lab = cv2.cvtColor(projection, cv2.COLOR_BGR2LAB).astype(np.float32)

        room_l = room_lab[:, :, 0][mask_bool]
        proj_l = proj_lab[:, :, 0][mask_bool]

        room_mean = np.mean(room_l)
        proj_mean = np.mean(proj_l)

        if proj_mean < 1:
            return projection

        # Nudge the tile toward the room's floor brightness but keep most of
        # the tile's own character. A full match (scale = room/proj) crushes a
        # bright marble 40% darker on a dark floor and washes dark slate out;
        # blending 65% toward the tile's own brightness keeps the selected
        # material looking like itself while still integrating with the scene.
        target = 0.35 * room_mean + 0.65 * proj_mean
        scale = float(np.clip(target / proj_mean, 0.85, 1.15))
        proj_lab[:, :, 0] = np.clip(proj_lab[:, :, 0] * scale, 0, 255)

        return cv2.cvtColor(proj_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
