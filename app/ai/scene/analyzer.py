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
        """Keep the stable lower/interior portion of a detected rug.

        Rug detections are often loose around the top edge. The floor-facing
        lower portion is the reliable obstruction to carve, so trim only the
        uncertain upper third while preserving the detected width and lower
        boundary.
        """
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
        """Subtract detected foreground objects and retain a protected mask."""
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
        table_boxes_mask = np.zeros_like(floor_mask)
        table_box_list: list[tuple[int, int, int, int]] = []
        floor_area = int((floor_mask > 0).sum())
        for detection, mask in zip(detections, masks):
            if mask.shape != floor_mask.shape:
                logger.warning("Ignoring obstruction mask with shape %s; expected %s.", mask.shape, floor_mask.shape)
                continue
            label = detection.label.lower()
            if "table" in label:
                x0, y0, x1, y1 = detection.box
                x0 = max(0, min(floor_mask.shape[1], int(x0)))
                x1 = max(x0, min(floor_mask.shape[1], int(x1)))
                y0 = max(0, min(floor_mask.shape[0], int(y0)))
                y1 = max(y0, min(floor_mask.shape[0], int(y1)))
                table_boxes_mask[y0:y1, x0:x1] = 255
                table_box_list.append((x0, y0, x1, y1))
            if "rug" in label:
                if floor_area > 0 and int((mask > 0).sum()) >= 0.5 * floor_area:
                    continue
                mask = self._conservative_rug_mask(mask, detection.box)
            obstruction = np.maximum(obstruction, mask)

        obstruction = cv2.bitwise_or(obstruction, table_boxes_mask)
        protected_mask = obstruction.copy()
        carve_mask = cv2.bitwise_and(obstruction, floor_mask)
        cleaned = cv2.subtract(floor_mask, carve_mask)
        return cleaned, table_box_list, protected_mask

    @staticmethod
    def _reclaim_under_tables(
        floor_mask: np.ndarray,
        depth: np.ndarray,
