"""Robust metric floor-plane estimation helpers for the v2.2 geometry path."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class MetricFloorResult:
    normal: np.ndarray
    centroid: np.ndarray
    equation: np.ndarray
    pitch: float
    roll: float
    residual_p95: float
    inlier_ratio: float


class MetricFloorEstimator:
    """Fit a stable floor plane while rejecting depth outliers.

    The semantic floor mask remains authoritative. Metric geometry is only
    allowed to score/refine pixels already supported by that mask.
    """

    def __init__(self, sample_size: int = 12000, iterations: int = 4, seed: int = 42) -> None:
        self.sample_size = sample_size
        self.iterations = iterations
        self.seed = seed

    @staticmethod
    def _focal(intrinsics) -> float:
        if intrinsics is not None:
            for name in ("fx", "focal_x"):
                value = getattr(intrinsics, name, None)
                if value is not None and float(value) > 1:
                    return float(value)
            if isinstance(intrinsics, dict):
                for name in ("fx", "focal_x"):
                    value = intrinsics.get(name)
                    if value is not None and float(value) > 1:
                        return float(value)
        return 0.9

    @staticmethod
    def _points_from_depth(depth: np.ndarray, focal: float) -> np.ndarray:
        depth = np.asarray(depth, dtype=np.float32)
        h, w = depth.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        cx = (w - 1) * 0.5
        cy = (h - 1) * 0.5
        z = np.maximum(depth, 1e-4)
        x = (xx.astype(np.float32) - cx) * z / max(focal, 1e-4)
        y = (yy.astype(np.float32) - cy) * z / max(focal, 1e-4)
        return np.stack((x, y, z), axis=-1)

    def estimate(self, floor_mask: np.ndarray, depth: np.ndarray, points=None, intrinsics=None) -> MetricFloorResult:
        mask = np.asarray(floor_mask) > 0
        depth = np.asarray(depth, dtype=np.float32)
        if depth.shape[:2] != mask.shape[:2]:
            raise ValueError("Metric depth and floor mask dimensions differ.")

        xyz = points
        if xyz is None:
            xyz = self._points_from_depth(depth, self._focal(intrinsics))
        xyz = np.asarray(xyz, dtype=np.float32)
        if xyz.ndim == 4 and xyz.shape[0] == 1:
            xyz = xyz[0]
        if xyz.shape[:2] != mask.shape[:2] or xyz.shape[-1] < 3:
            raise ValueError("Metric point cloud dimensions are invalid.")
        xyz = xyz[..., :3]

        valid = mask & np.isfinite(xyz).all(axis=2)
        valid &= np.linalg.norm(xyz, axis=2) > 1e-6
        ys, xs = np.where(valid)
        if len(xs) < 100:
            raise ValueError("Floor mask contains too few valid metric points.")

        pts = xyz[ys, xs]
        rng = np.random.default_rng(self.seed)
        if len(pts) > self.sample_size:
            pts = pts[rng.choice(len(pts), self.sample_size, replace=False)]

        keep = np.ones(len(pts), dtype=bool)
        normal = np.zeros(3, dtype=np.float32)
        centroid = pts.mean(axis=0)
        for _ in range(self.iterations):
            sample = pts[keep]
            if len(sample) < 100:
                sample = pts
            centroid = sample.mean(axis=0)
            _, _, vh = np.linalg.svd(sample - centroid, full_matrices=False)
            normal = vh[-1].astype(np.float32)
            normal /= max(float(np.linalg.norm(normal)), 1e-8)
            residual = np.abs((pts - centroid) @ normal)
            threshold = max(0.008, min(0.08, float(np.percentile(residual, 85)) * 1.75))
            keep = residual <= threshold

        d = -float(np.dot(normal, centroid))
        equation = np.array([normal[0], normal[1], normal[2], d], dtype=np.float32)
        all_residual = np.abs(np.tensordot(xyz, normal, axes=([2], [0])) + d)
        floor_residual = all_residual[mask & np.isfinite(all_residual)]
        p95 = float(np.percentile(floor_residual, 95)) if floor_residual.size else 0.0
        inlier_ratio = float(np.mean(all_residual[valid] <= max(0.01, p95 * 1.25))) if valid.any() else 0.0

        # Orient the normal consistently toward the camera-facing half-space.
        if normal[2] > 0:
            normal = -normal
            equation[:3] = normal
            equation[3] = -float(np.dot(normal, centroid))

        pitch = float(np.degrees(np.arctan2(normal[1], max(abs(float(normal[2])), 1e-6))))
        roll = float(np.degrees(np.arctan2(normal[0], max(abs(float(normal[2])), 1e-6))))
        return MetricFloorResult(
            normal=normal.astype(np.float32),
            centroid=centroid.astype(np.float32),
            equation=equation.astype(np.float32),
            pitch=pitch,
            roll=roll,
            residual_p95=p95,
            inlier_ratio=inlier_ratio,
        )
