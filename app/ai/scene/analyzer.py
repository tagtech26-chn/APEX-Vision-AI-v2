"""Scene analysis orchestration and provider factory."""

from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np

from app.ai.config import heavy_models_available, resolve_provider
from app.ai.depth.base import DepthEstimator
from app.ai.detection.base import Detection, ObjectDetector
from app.ai.geometry.homography import HomographyEngine
from app.ai.geometry.plane import PlaneEstimator, PlaneResult
from app.ai.geometry.polygon import PolygonEngine
from app.ai.scene.result import SceneResult
from app.ai.segmentation.base import Segmenter

logger = logging.getLogger("apex.ai")


class SceneAnalyzer:
    """Runs detection -> segmentation -> depth -> geometry to build a SceneResult."""

    def __init__(self, detector: ObjectDetector, segmenter: Segmenter, depth: DepthEstimator) -> None:
        self.detector = detector
        self.segmenter = segmenter
        self.depth = depth
        self.polygon_engine = PolygonEngine()
        self.homography_engine = HomographyEngine()
        self.plane_estimator = PlaneEstimator()

    @property
    def providers(self) -> dict[str, str]:
        return {"detector": self.detector.name, "segmenter": self.segmenter.name, "depth": self.depth.name}

    @staticmethod
    def _downscale(image: np.ndarray, max_dim: int | None = None) -> np.ndarray:
        from app.core.config import settings
        limit = max_dim or settings.render_max_dim
        height, width = image.shape[:2]
        largest = max(height, width)
        if largest <= limit:
            return image
        scale = limit / largest
        return cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)

    @staticmethod
    def _conservative_rug_mask(mask: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
        """Keep the reliable lower/interior portion of a loose rug detection."""
        x0, y0, x1, y1 = [int(v) for v in box]
        height = max(1, y1 - y0)
        trim = max(1, int(round(height * 0.33)))
        result = np.zeros_like(mask)
        start_y = max(0, min(mask.shape[0], y0 + trim))
        end_y = max(start_y, min(mask.shape[0], y1))
        start_x = max(0, min(mask.shape[1], x0))
        end_x = max(start_x, min(mask.shape[1], x1))
        result[start_y:end_y, start_x:end_x] = mask[start_y:end_y, start_x:end_x]
        return result

    def _carve_obstructions(
        self,
        image: np.ndarray,
        floor_mask: np.ndarray,
    ) -> tuple[np.ndarray, list[tuple[int, int, int, int]], np.ndarray]:
        """Subtract detected foreground objects and return their protected mask."""
        empty = np.zeros_like(floor_mask)
        if not hasattr(self.segmenter, "segment_many"):
            return floor_mask, [], empty
        try:
            detections = self.detector.detect(
                image,
                "sofa. couch. armchair. chair. table. rug. plant. lamp. cabinet. bed. furniture.",
            )
        except Exception as exc:
            logger.warning("Obstruction detection failed (%s); skipping carve.", exc)
            return floor_mask, [], empty
        boxes = [d.box for d in detections]
        if not boxes:
            return floor_mask, [], empty
        try:
            masks = self.segmenter.segment_many(image, boxes=boxes)
        except Exception as exc:
            logger.warning("Obstruction segmentation failed (%s); skipping carve.", exc)
            return floor_mask, [], empty

        obstruction = np.zeros_like(floor_mask)
        protected_mask = np.zeros_like(floor_mask)
        table_boxes_mask = np.zeros_like(floor_mask)
        table_box_list: list[tuple[int, int, int, int]] = []
        floor_area = int((floor_mask > 0).sum())
        for detection, mask in zip(detections, masks):
            if mask.shape != floor_mask.shape:
                logger.warning("Ignoring obstruction mask with shape %s; expected %s.", mask.shape, floor_mask.shape)
                continue

            label = detection.label.lower()
            original_mask = mask
            protected_mask = np.maximum(protected_mask, original_mask)

            if "table" in label:
                x0, y0, x1, y1 = detection.box
                x0 = max(0, min(floor_mask.shape[1], int(x0)))
                x1 = max(x0, min(floor_mask.shape[1], int(x1)))
                y0 = max(0, min(floor_mask.shape[0], int(y0)))
                y1 = max(y0, min(floor_mask.shape[0], int(y1)))
                table_boxes_mask[y0:y1, x0:x1] = 255
                table_box_list.append((x0, y0, x1, y1))

            if "rug" in label:
                rug_area = int((mask > 0).sum())
                if floor_area > 0 and rug_area >= 0.5 * floor_area:
                    logger.info("Skipping floor-scale rug (%.0f%% of floor).", 100.0 * rug_area / floor_area)
                    continue
                mask = self._conservative_rug_mask(mask, detection.box)

            obstruction = np.maximum(obstruction, mask)

        obstruction = cv2.bitwise_or(obstruction, table_boxes_mask)
        protected_mask = cv2.bitwise_or(protected_mask, table_boxes_mask)
        carve_mask = cv2.bitwise_and(obstruction, floor_mask)
        cleaned = cv2.subtract(floor_mask, carve_mask)
        return cleaned, table_box_list, protected_mask

    @staticmethod
    def _reclaim_under_tables(
        floor_mask: np.ndarray,
        depth: np.ndarray,
        plane: PlaneResult,
        table_boxes: list[tuple[int, int, int, int]],
    ) -> np.ndarray:
        """Restore floor that full-box table carving over-removed."""
        if not table_boxes or depth is None:
            return floor_mask
        n0, n1, n2, d = plane.equation
        ys, xs = np.mgrid[0 : floor_mask.shape[0], 0 : floor_mask.shape[1]]
        resid = np.abs(n0 * xs + n1 * ys + n2 * depth.astype(np.float32) + d)
        floor_resid = resid[floor_mask > 0]
        if floor_resid.size < 100:
            return floor_mask
        tolerance = float(np.percentile(floor_resid, 95))
        seeds = cv2.dilate(floor_mask, np.ones((3, 3), np.uint8)) > 0
        result = floor_mask.copy()
        for x0, y0, x1, y1 in table_boxes:
            candidates = np.zeros_like(floor_mask, dtype=bool)
            candidates[y0:y1, x0:x1] = (resid[y0:y1, x0:x1] <= tolerance) & (floor_mask[y0:y1, x0:x1] == 0)
            if not candidates.any():
                continue
            count, labels, _, _ = cv2.connectedComponentsWithStats(candidates.astype(np.uint8), connectivity=8)
            for idx in range(1, count):
                if (seeds & (labels == idx)).any():
                    result[labels == idx] = 255
        return result

    @staticmethod
    def _fill_floor_notches(mask: np.ndarray, image: np.ndarray) -> np.ndarray:
        """Fill narrow dips in the floor-mask top edge (heavy stack only)."""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        lightness = lab[:, :, 0].astype(np.int16)
        binary = mask > 0
        height, width = binary.shape
        top = np.full(width, height, dtype=np.int32)
        for x in range(width):
            rows = np.where(binary[:, x])[0]
            if len(rows):
                top[x] = rows[0]
        run_min = top.copy()
        for x in range(width):
            lo = max(0, x - 60)
            hi = min(width, x + 61)
            run_min[x] = int(top[lo:hi].min())
        is_dip = (top < height) & ((top - run_min) > 15)
        keep = np.zeros(width, bool)
        x = 0
        while x < width:
            if is_dip[x]:
                x0 = x
                while x + 1 < width and is_dip[x + 1]:
                    x += 1
                x1 = x
                if x1 - x0 + 1 <= 90:
                    keep[x0 : x1 + 1] = True
            x += 1
        filled = binary.copy()
        for x in np.where(keep)[0]:
            y_floor = int(top[x])
            y_top = int(run_min[x])
            if y_top >= y_floor:
                continue
            y = y_floor
            while y > y_top and lightness[y - 1, x] >= 20:
                y -= 1
            if y < y_floor:
                filled[y:y_floor, x] = True
        return (filled * 255).astype(np.uint8)

    @staticmethod
    def _largest_component(mask: np.ndarray) -> np.ndarray:
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
        if count <= 1:
            return mask
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        result = np.zeros(mask.shape, dtype=np.uint8)
        result[labels == largest] = 255
        return result

    def analyze(self, image_path: str | Path, progress_cb=None) -> SceneResult:
        image_path = Path(image_path)
        image = cv2.imread(str(image_path))
        if image is None:
            raise FileNotFoundError(f"Cannot load image: {image_path}")
        image = self._downscale(image)
        logger.info("Analysis image: %s (%dx%d)", image_path.name, image.shape[1], image.shape[0])

        def report(fraction: float, message: str) -> None:
            if progress_cb is not None:
                progress_cb(fraction, message)

        report(0.05, "Loading AI models...")
        height, width = image.shape[:2]
        scene = SceneResult()
        scene.image = image
        scene.width = width
        scene.height = height
        scene.metadata["providers"] = self.providers

        report(0.15, "Detecting floor...")
        detection = self.detector.detect_floor(image)
        logger.info("Floor detected with %s: %s", self.detector.name, detection)
        report(0.35, "Segmenting floor...")
        floor_mask = self.segmenter.segment(image, box=detection.box)
        if hasattr(self.segmenter, "segment_many"):
            floor_mask = self._fill_floor_notches(floor_mask, image)
        floor_mask, table_boxes, protected_mask = self._carve_obstructions(image, floor_mask)
        scene.floor_mask = floor_mask
        scene.protected_object_mask = protected_mask
        scene.metadata["occlusion"] = {"provider": self.detector.name, "protected_pixels": int((protected_mask > 0).sum()), "enabled": bool((protected_mask > 0).any())}
        logger.info("Floor mask built with %s; protected object pixels=%d", self.segmenter.name, int((protected_mask > 0).sum()))

        report(0.55, "Building depth map...")
        depth = self.depth.predict(image)
        scene.depth_map = depth
        logger.info("Depth map built with %s", self.depth.name)
        report(0.7, "Extracting floor geometry...")
        plane = self.plane_estimator.estimate(floor_mask, depth)
        scene.floor_plane.normal = plane.normal
        scene.floor_plane.distance = float(plane.equation[3])
        scene.camera_pose.pitch = plane.pitch
        scene.camera_pose.roll = plane.roll
        if table_boxes:
            floor_mask = self._reclaim_under_tables(floor_mask, depth, plane, table_boxes)
            scene.floor_mask = floor_mask
            logger.info("Reclaimed floor under %d table box(es).", len(table_boxes))
        report(0.82, "Finalising floor mask...")
        polygon = self.polygon_engine.extract(floor_mask)
        scene.floor_polygon = polygon
        logger.info("Floor polygon extracted: %s", polygon.tolist())
        homography = self.homography_engine.compute(polygon)
        scene.homography = homography.matrix
        report(0.9, "Scene ready")
        return scene


def build_scene_analyzer(provider: str | None = None) -> SceneAnalyzer:
    """Build a SceneAnalyzer using the requested (or auto) provider stack."""
    provider = resolve_provider(provider)
    if provider == "auto":
        available, missing = heavy_models_available()
        if available:
            provider = "heavy"
            logger.info("Auto mode: heavy AI stack selected.")
        else:
            provider = "light"
            logger.info("Auto mode: heavy AI stack unavailable (%s); using heuristics.", ", ".join(missing))
    if provider == "heavy":
        try:
            return _build_heavy()
        except Exception as exc:
            logger.warning("Heavy AI stack failed to initialise (%s); falling back to heuristics.")
            return _build_light()
    if provider == "light":
        return _build_light()
    raise RuntimeError(f"Unhandled provider: {provider}")


def _build_heavy() -> SceneAnalyzer:
    from app.ai.depth.depth_anything import DepthAnythingProvider
    from app.ai.detection.grounding_dino import GroundingDINOProvider
    from app.ai.segmentation.sam2 import SAM2Provider
    return SceneAnalyzer(detector=GroundingDINOProvider(), segmenter=SAM2Provider(), depth=DepthAnythingProvider())


def _build_light() -> SceneAnalyzer:
    from app.ai.depth.heuristic import HeuristicDepth
    from app.ai.detection.heuristic import HeuristicDetector
    from app.ai.segmentation.heuristic import HeuristicSegmenter
    return SceneAnalyzer(detector=HeuristicDetector(), segmenter=HeuristicSegmenter(), depth=HeuristicDepth())
