"""V2.2 scene analyzer: semantic floor segmentation + metric geometry.

The design rule is strict: metric depth can remove or score pixels already
supported by semantic floor segmentation, but it cannot manufacture a new
floor region. Protected objects are removed again after every refinement step.
"""

from __future__ import annotations

import logging

import cv2
import numpy as np

from app.ai.geometry.metric_floor import MetricFloorEstimator
from app.ai.scene.analyzer import SceneAnalyzer

logger = logging.getLogger("apex.ai")


class V22SceneAnalyzer(SceneAnalyzer):
    """Refine the existing scene with metric floor geometry and guardrails."""

    def __init__(self, detector, segmenter, depth) -> None:
        super().__init__(detector=detector, segmenter=segmenter, depth=depth)
        self.metric_floor = MetricFloorEstimator()

    @staticmethod
    def _normal_consistency_mask(
        normals: np.ndarray | None,
        seed_mask: np.ndarray,
        minimum_cosine: float = 0.82,
    ) -> np.ndarray:
        if normals is None or normals.shape[:2] != seed_mask.shape[:2]:
            return np.ones(seed_mask.shape, dtype=bool)
        valid = (seed_mask > 0) & np.isfinite(normals).all(axis=2)
        if int(valid.sum()) < 100:
            return np.ones(seed_mask.shape, dtype=bool)
        samples = normals[valid].astype(np.float32)
        lengths = np.linalg.norm(samples, axis=1)
        samples = samples[lengths > 1e-5]
        if len(samples) < 100:
            return np.ones(seed_mask.shape, dtype=bool)
        target = np.median(samples, axis=0)
        target /= max(float(np.linalg.norm(target)), 1e-6)
        cosine = np.sum(normals.astype(np.float32) * target[None, None, :], axis=2)
        positive = cosine >= minimum_cosine
        negative = cosine <= -minimum_cosine
        return negative if int((negative & valid).sum()) > int((positive & valid).sum()) else positive

    @staticmethod
    def _stable_top_boundary(seed: np.ndarray, radius: int = 35) -> np.ndarray:
        """Return a conservative top-of-floor boundary for every image column."""
        binary = seed > 0
        h, w = binary.shape
        top = np.full(w, h, dtype=np.int32)
        for x in range(w):
            rows = np.flatnonzero(binary[:, x])
            if rows.size:
                top[x] = int(rows[0])

        valid = top < h
        if not valid.any():
            return top

        filled = top.copy()
        valid_values = top[valid]
        fallback = int(np.percentile(valid_values, 25))
        filled[~valid] = fallback

        smooth = filled.copy()
        for x in range(w):
            lo = max(0, x - radius)
            hi = min(w, x + radius + 1)
            smooth[x] = int(np.percentile(filled[lo:hi], 35))

        # Never move the boundary upward by a large amount. This is a guard
        # against accidental wall contamination, not a new floor detector.
        return np.maximum(smooth, top - 18)

    @staticmethod
    def _remove_protected(mask: np.ndarray, protected: np.ndarray | None) -> np.ndarray:
        if protected is None or not (protected > 0).any():
            return mask
        protected_band = cv2.dilate(
            (protected > 0).astype(np.uint8) * 255,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
        )
        return cv2.bitwise_and(mask, cv2.bitwise_not(protected_band))

    @classmethod
    def _refine_floor_mask(
        cls,
        seed: np.ndarray,
        residual: np.ndarray,
        normals: np.ndarray | None,
        residual_threshold: float,
        protected: np.ndarray | None = None,
    ) -> np.ndarray:
        seed_bool = seed > 0
        refined = seed_bool & np.isfinite(residual) & (residual <= residual_threshold)

        # Keep the semantic floor's upper envelope stable. This prevents a
        # noisy segmentation notch from becoming a wall-sized tile region.
        boundary = cls._stable_top_boundary(seed)
        yy = np.arange(seed.shape[0], dtype=np.int32)[:, None]
        refined &= yy >= boundary[None, :]

        if normals is not None and normals.shape[:2] == seed.shape[:2]:
            refined &= cls._normal_consistency_mask(normals, refined)

        result = refined.astype(np.uint8) * 255
        result = cv2.morphologyEx(
            result,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )
        result = cv2.morphologyEx(
            result,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
        )
        result = cv2.bitwise_and(result, seed.astype(np.uint8))
        result = cls._remove_protected(result, protected)

        if (result > 0).any():
            result = cls._largest_component(result)
        return result

    @staticmethod
    def _largest_component(mask: np.ndarray) -> np.ndarray:
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        if count <= 1:
            return mask
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        result = np.zeros(mask.shape, dtype=np.uint8)
        result[labels == largest] = 255
        return result

    def analyze(self, image_path, progress_cb=None):
        scene = super().analyze(image_path, progress_cb=progress_cb)
        metric_depth = getattr(self.depth, "last_metric_depth", None)
        if metric_depth is None:
            metric_depth = scene.depth_map
        if metric_depth is None:
            raise RuntimeError("V2.2 geometry requires a metric-depth provider.")

        points = getattr(self.depth, "last_points", None)
        intrinsics = getattr(self.depth, "last_intrinsics", None)
        normals = getattr(self.depth, "last_normals", None)
        metric = self.metric_floor.estimate(
            scene.floor_mask,
            metric_depth,
            points=points,
            intrinsics=intrinsics,
        )

        if points is not None:
            xyz = np.asarray(points, dtype=np.float32)
            if xyz.ndim == 4 and xyz.shape[0] == 1:
                xyz = xyz[0]
            xyz = xyz[..., :3]
        else:
            xyz = self.metric_floor._points_from_depth(
                metric_depth,
                self.metric_floor._focal(intrinsics),
            )

        residual = np.abs(
            np.tensordot(xyz, metric.normal, axes=([2], [0])) + metric.equation[3]
        )
        floor_residual = residual[scene.floor_mask > 0]
        if floor_residual.size:
            p90 = float(np.percentile(floor_residual, 90))
            p97 = float(np.percentile(floor_residual, 97))
            threshold = min(max(p90 * 1.75, 0.012), max(p97 * 1.25, 0.025), 0.10)
        else:
            threshold = 0.05

        original_area = int((scene.floor_mask > 0).sum())
        protected = scene.protected_object_mask
        refined = self._refine_floor_mask(
            scene.floor_mask,
            residual,
            normals,
            threshold,
            protected=protected,
        )
        refined_area = int((refined > 0).sum())

        # Geometry must never destroy a usable semantic floor. If refinement
        # becomes too aggressive, retain the semantic floor but still remove
        # explicitly protected objects.
        minimum_area = max(250, int(original_area * 0.12))
        if original_area >= 500 and refined_area < minimum_area:
            logger.warning(
                "[V2.2] Metric refinement rejected: area collapsed %d -> %d pixels.",
                original_area,
                refined_area,
            )
            refined = self._remove_protected(scene.floor_mask.copy(), protected)
            refined_area = int((refined > 0).sum())

        polygon = self.polygon_engine.extract(refined)
        homography = self.homography_engine.compute(polygon)
        scene.floor_mask = refined
        scene.floor_polygon = polygon
        scene.homography = homography.matrix
        scene.floor_plane.normal = metric.normal
        scene.floor_plane.distance = float(metric.equation[3])
        scene.camera_pose.pitch = metric.pitch
        scene.camera_pose.roll = metric.roll

        scene.metadata["v22_geometry"] = {
            "version": "2.2-geometry-safe",
            "depth_provider": self.depth.name,
            "segmenter": self.segmenter.name,
            "metric_depth_fallback": bool(getattr(self.depth, "used_fallback", False)),
            "metric_plane_residual_p95_m": metric.residual_p95,
            "metric_plane_inlier_ratio": metric.inlier_ratio,
            "metric_plane_threshold_m": threshold,
            "metric_points": points is not None,
            "surface_normals": normals is not None,
            "semantic_area_px": original_area,
            "refined_area_px": refined_area,
            "refined_area_ratio": (refined_area / original_area) if original_area else 0.0,
            "protected_pixels": int((protected > 0).sum()) if protected is not None else 0,
            "bottom_edge_forced": False,
        }
        return scene
