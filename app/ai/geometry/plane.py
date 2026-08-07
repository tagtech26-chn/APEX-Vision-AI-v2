"""Plane fitting over the floor depth points."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class PlaneResult:
    normal: np.ndarray
    centroid: np.ndarray
    equation: np.ndarray
    pitch: float
    roll: float


class PlaneEstimator:
    """Fits a plane to sampled floor pixels using SVD."""

    def __init__(self, sample_size: int = 5000, seed: int = 42) -> None:
        self.sample_size = sample_size
        self.seed = seed

    def estimate(
        self,
        floor_mask: np.ndarray,
        depth: np.ndarray,
    ) -> PlaneResult:
        mask = floor_mask > 0
        ys, xs = np.where(mask)

        if len(xs) < 100:
            raise ValueError("Floor mask contains too few pixels.")

        sample_size = min(self.sample_size, len(xs))
        rng = np.random.default_rng(self.seed)
        indices = rng.choice(len(xs), sample_size, replace=False)

        xs = xs[indices]
        ys = ys[indices]

        z = depth[ys, xs]
        points = np.column_stack(
            (
                xs.astype(np.float32),
                ys.astype(np.float32),
                z.astype(np.float32),
            )
        )

        centroid = points.mean(axis=0)
        centered = points - centroid

        _, _, vh = np.linalg.svd(centered, full_matrices=False)
        normal = vh[-1]
        norm = np.linalg.norm(normal)
        if norm == 0:
            raise ValueError("Degenerate plane fit.")
        normal = normal / norm

        d = -np.dot(normal, centroid)
        equation = np.array([normal[0], normal[1], normal[2], d], dtype=np.float32)

        pitch = float(np.degrees(np.arctan2(normal[1], normal[2])))
        roll = float(np.degrees(np.arctan2(normal[0], normal[2])))

        return PlaneResult(
            normal=normal.astype(np.float32),
            centroid=centroid.astype(np.float32),
            equation=equation,
            pitch=pitch,
            roll=roll,
        )
