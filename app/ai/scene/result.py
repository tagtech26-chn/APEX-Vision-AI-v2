"""Scene result data structures."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True)
class CameraPose:
    pitch: float = 0.0
    roll: float = 0.0
    yaw: float = 0.0


@dataclass(slots=True)
class FloorPlane:
    normal: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    distance: float = 0.0


@dataclass(slots=True)
class SceneResult:
    image: np.ndarray | None = None
    width: int = 0
    height: int = 0

    # AI outputs
    floor_mask: np.ndarray | None = None
    wall_mask: np.ndarray | None = None
    ceiling_mask: np.ndarray | None = None
    depth_map: np.ndarray | None = None

    # Geometry
    floor_polygon: np.ndarray | None = None
    homography: np.ndarray | None = None

    camera_pose: CameraPose = field(default_factory=CameraPose)
    floor_plane: FloorPlane = field(default_factory=FloorPlane)

    metadata: dict = field(default_factory=dict)

    @property
    def size(self) -> tuple[int, int]:
        return self.width, self.height

    @property
    def has_depth(self) -> bool:
        return self.depth_map is not None

    @property
    def has_floor(self) -> bool:
        return self.floor_mask is not None

    @property
    def has_polygon(self) -> bool:
        return self.floor_polygon is not None

    @property
    def is_complete(self) -> bool:
        return (
            self.image is not None
            and self.floor_mask is not None
            and self.depth_map is not None
            and self.floor_polygon is not None
            and self.homography is not None
        )
