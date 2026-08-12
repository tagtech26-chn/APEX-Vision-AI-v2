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

    @staticmethod
    def _carve_metric_outliers(
        floor_mask: np.ndarray,
        residual: np.ndarray,
        protected: np.ndarray | None,
    ) -> tuple[np.ndarray, np.ndarray, dict[str, float | int]]:
        """Remove large depth-inconsistent foreground regions from the floor.

        This is intentionally a second safety pass after semantic segmentation.
        A sofa, chair, table, rug edge or similar foreground region can have
        colours close enough to the floor to survive a lightweight segmenter.
        If its depth is inconsistent with the estimated floor plane, it becomes
        an occlusion candidate. Depth never adds pixels to the floor here.
        """
        mask = floor_mask.astype(np.uint8).copy()
        existing = mask > 0
        values = residual[existing & np.isfinite(residual)]
        diagnostics: dict[str, float | int] = {
            "outlier_threshold_m": 0.0,
            "outlier_components": 0,
            "outlier_pixels": 0,
        }
        if values.size < 500:
            return mask, protected if protected is not None else np.zeros_like(mask), diagnostics

        median = float(np.median(values))
        mad = float(np.median(np.abs(values - median)))
        robust_sigma = max(1.4826 * mad, 0.001)
        p97 = float(np.percentile(values, 97))
        threshold = max(median + 6.0 * robust_sigma, p97 * 1.15, 0.025)
        threshold = min(threshold, 0.10)
        diagnostics["outlier_threshold_m"] = threshold

        candidate = existing & np.isfinite(residual) & (residual > threshold)
        h, w = mask.shape
        boundary = V22SceneAnalyzer._stable_top_boundary(mask)
        yy = np.arange(h, dtype=np.int32)[:, None]
        candidate &= yy >= boundary[None, :]

        candidate_mask = candidate.astype(np.uint8) * 255
        candidate_mask = cv2.morphologyEx(
            candidate_mask,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
            iterations=1,
        )
        candidate_mask = cv2.morphologyEx(
            candidate_mask,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
            iterations=1,
        )

        count, labels, stats, _ = cv2.connectedComponentsWithStats(candidate_mask, connectivity=8)
        floor_area = int(existing.sum())
        min_area = max(400, int(floor_area * 0.001))
        max_area = int(floor_area * 0.45)
        remove = np.zeros_like(mask)

        accepted = 0
        for idx in range(1, count):
            area = int(stats[idx, cv2.CC_STAT_AREA])
            if area < min_area or area > max_area:
                continue

            x = int(stats[idx, cv2.CC_STAT_LEFT])
            y = int(stats[idx, cv2.CC_STAT_TOP])
            cw = int(stats[idx, cv2.CC_STAT_WIDTH])
            ch = int(stats[idx, cv2.CC_STAT_HEIGHT])

            # A region touching the very bottom is likely genuine floor that
            # has high residual from image-edge noise; keep it conservative.
            if y + ch >= h - 2:
                continue
            if cw >= int(w * 0.92) and ch >= int(h * 0.15):
                continue

            remove[labels == idx] = 255
            accepted += 1

        if not (remove > 0).any():
            return mask, protected if protected is not None else np.zeros_like(mask), diagnostics

        cleaned = cv2.bitwise_and(mask, cv2.bitwise_not(remove))
        cleaned = cv2.bitwise_and(cleaned, cv2.bitwise_not(protected if protected is not None else np.zeros_like(mask)))

        protected_out = protected.copy() if protected is not None else np.zeros_like(mask)
        protected_out = cv2.bitwise_or(protected_out, remove)
        protected_out = cv2.dilate(
            protected_out,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )

        diagnostics["outlier_components"] = accepted
        diagnostics["outlier_pixels"] = int((remove > 0).sum())
        return cleaned, protected_out, diagnostics

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

        # New V2.2 safety pass: find foreground regions that accidentally
        # survived semantic segmentation because their colours resemble floor.
        # This pass only removes depth outliers; it never expands the floor.
        floor_before_outlier = scene.floor_mask.copy()
        floor_after_outlier, protected, outlier_diag = self._carve_metric_outliers(
            floor_before_outlier,
            residual,
            scene.protected_object_mask,
        )

        removed_ratio = (
            float((floor_before_outlier > 0).sum() - (floor_after_outlier > 0).sum())
            / max(float((floor_before_outlier > 0).sum()), 1.0)
        )

        # Only accept the outlier pass when it does not collapse the floor.
        if removed_ratio <= 0.55 and int((floor_after_outlier > 0).sum()) >= 500:
            scene.floor_mask = floor_after_outlier
            scene.protected_object_mask = protected
            if removed_ratio > 0.0:
                logger.info(
                    "[V2.2] Metric foreground protection removed %.2f%% of semantic floor pixels.",
                    removed_ratio * 100.0,
                )

                # Refit the plane after removing foreground depth outliers.
                metric = self.metric_floor.estimate(
                    scene.floor_mask,
                    metric_depth,
                    points=points,
                    intrinsics=intrinsics,
                )
                residual = np.abs(
                    np.tensordot(xyz, metric.normal, axes=([2], [0])) + metric.equation[3]
                )
        else:
            protected = scene.protected_object_mask if scene.protected_object_mask is not None else np.zeros_like(scene.floor_mask)
            outlier_diag["rejected"] = 1

        floor_residual = residual[scene.floor_mask > 0]
        if floor_residual.size:
            p90 = float(np.percentile(floor_residual, 90))
            p97 = float(np.percentile(floor_residual, 97))
            threshold = min(max(p90 * 1.75, 0.012), max(p97 * 1.25, 0.025), 0.10)
        else:
            threshold = 0.05

        original_area = int((scene.floor_mask > 0).sum())
        refined = self._refine_floor_mask(
            scene.floor_mask,
            residual,
            normals,
            threshold,
            protected=protected,
        )
        refined_area = int((refined > 0).sum())

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

        # V2.3-ready surface slots: we do not render walls/ceiling yet, but the
        # scene contract already exposes these regions so the next surface-aware
        # analyzer can add them without changing the renderer API.
        scene.metadata["surfaces"] = {
            "floor": {"enabled": True, "mask": "floor_mask"},
            "wall": {"enabled": False, "mask": "wall_mask"},
            "ceiling": {"enabled": False, "mask": "ceiling_mask"},
            "countertop": {"enabled": False},
            "backsplash": {"enabled": False},
            "other": {"enabled": False},
        }

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
            "metric_outlier_threshold_m": outlier_diag.get("outlier_threshold_m", 0.0),
            "metric_outlier_components": outlier_diag.get("outlier_components", 0),
            "metric_outlier_pixels": outlier_diag.get("outlier_pixels", 0),
            "bottom_edge_forced": False,
        }
        return scene
