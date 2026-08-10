"""Tests for the scene analyzer (lightweight provider stack)."""

from __future__ import annotations

import cv2
import numpy as np

from app.ai.scene.analyzer import build_scene_analyzer, SceneAnalyzer
from app.ai.detection.base import Detection
from app.ai.geometry.plane import PlaneEstimator
from app.ai.segmentation.base import Segmenter


def test_light_analyzer_pipeline(room_image_path):
    analyzer = build_scene_analyzer("light")
    assert analyzer.providers["detector"] == "heuristic"
    assert analyzer.providers["segmenter"] == "heuristic"
    assert analyzer.providers["depth"] == "heuristic"

    scene = analyzer.analyze(room_image_path)

    assert scene.width > 0
    assert scene.height > 0
    assert scene.floor_mask is not None
    assert scene.depth_map is not None
    assert scene.floor_polygon is not None
    assert scene.floor_polygon.shape == (4, 2)
    assert scene.homography is not None
    assert scene.is_complete


def test_analyzer_raises_on_missing_file(tmp_path):
    analyzer = build_scene_analyzer("light")
    try:
        analyzer.analyze(tmp_path / "missing.png")
        raised = False
    except FileNotFoundError:
        raised = True
    assert raised


def test_depth_is_normalised(room_image_path):
    analyzer = build_scene_analyzer("light")
    scene = analyzer.analyze(room_image_path)
    assert scene.depth_map.dtype == np.float32
    assert scene.depth_map.min() >= 0.0
    assert scene.depth_map.max() <= 1.0


def test_light_floor_mask_covers_floor(room_image_path):
    from app.ai.segmentation.heuristic import estimate_floor_mask

    image = cv2.imread(str(room_image_path))
    mask = estimate_floor_mask(image)

    floor = np.zeros(image.shape[:2], dtype=np.uint8)
    pts = np.array([[140, 420], [500, 420], [620, 479], [20, 479]], dtype=np.int32)
    cv2.fillConvexPoly(floor, pts, 255)

    assert (mask[floor > 0] > 0).mean() > 0.9
    assert (mask[:400] > 0).mean() < 0.05


def test_texture_carve_removes_patterned_rug():
    from app.ai.segmentation.heuristic import estimate_floor_mask

    image = np.zeros((240, 320, 3), dtype=np.uint8)
    image[:, :] = (90, 120, 150)

    rng = np.random.default_rng(0)
    rug_colour = np.full((100, 120, 3), (95, 125, 155), dtype=np.int16)
    noise = rng.integers(-45, 45, (100, 120, 3))
    image[80:180, 100:220] = np.clip(rug_colour + noise, 0, 255).astype(np.uint8)

    mask = estimate_floor_mask(image)
    rug = np.zeros(image.shape[:2], dtype=np.uint8)
    rug[80:180, 100:220] = 255

    assert (mask[rug > 0] > 0).mean() < 0.5
    assert (mask > 0).sum() > 0.5 * image.shape[0] * image.shape[1]


def test_light_floor_polygon_has_perspective(room_image_path):
    analyzer = build_scene_analyzer("light")
    scene = analyzer.analyze(room_image_path)

    tl, tr, br, bl = scene.floor_polygon
    top_width = abs(float(tr[0]) - float(tl[0]))
    bottom_width = abs(float(br[0]) - float(bl[0]))
    assert bottom_width > top_width


class _FakeDetector:
    name = "fake"

    def detect(self, image, prompt):
        if prompt == "floor":
            return [Detection(label="floor", score=1.0, box=(0, 0, 300, 300))]
        return [
            Detection(label="sofa", score=0.9, box=(10, 20, 40, 50)),
            Detection(label="rug", score=0.8, box=(100, 100, 250, 250)),
        ]


class _FakeSegmenter:
    name = "fake"

    def segment(self, image, box=None, points=None):
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        if box is not None:
            x1, y1, x2, y2 = box
            mask[y1:y2, x1:x2] = 255
        return mask

    def segment_many(self, image, boxes=None, points=None):
        return [self.segment(image, box=box) for box in boxes or []]


def test_obstruction_carve_subtracts_furniture():
    analyzer = SceneAnalyzer(_FakeDetector(), _FakeSegmenter(), depth=None)
    image = np.zeros((300, 300, 3), dtype=np.uint8)
    floor_mask = np.full((300, 300), 255, dtype=np.uint8)

    result, table_boxes, protected_mask = analyzer._carve_obstructions(image, floor_mask)

    assert (result[20:50, 10:40] == 0).all()
    assert (result[149:200, 100:250] == 0).all()
    assert (result[100:148, 100:250] > 0).all()
    assert (result[240:290, 240:290] > 0).all()
    assert table_boxes == []
    assert protected_mask.shape == floor_mask.shape
    assert (protected_mask[20:50, 10:40] == 255).all()
    assert (protected_mask[100:250, 100:250] == 255).all()


def test_obstruction_carve_table_box_stays_solid():
    class _TableDetector(_FakeDetector):
        def detect(self, image, prompt):
            if prompt == "floor":
                return [Detection(label="floor", score=1.0, box=(0, 0, 300, 300))]
            return [Detection(label="table", score=0.9, box=(50, 50, 250, 250))]

    class _PartialMaskSegmenter(_FakeSegmenter):
        def segment(self, image, box=None, points=None):
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            if box is not None:
                x1, y1, x2, y2 = box
                mask[y1 : y1 + 80, x1 : x1 + 80] = 255
            return mask

    analyzer = SceneAnalyzer(_TableDetector(), _PartialMaskSegmenter(), depth=None)
    image = np.zeros((300, 300, 3), dtype=np.uint8)
    floor_mask = np.full((300, 300), 255, dtype=np.uint8)

    result, table_boxes, protected_mask = analyzer._carve_obstructions(image, floor_mask)

    assert (result[50:250, 50:250] == 0).all()
    assert table_boxes == [(50, 50, 250, 250)]
    assert (protected_mask[50:250, 50:250] == 255).all()


def test_obstruction_carve_skipped_without_segment_many():
    class _PlainSegmenter(Segmenter):
        name = "plain"

        def segment(self, image, box=None, points=None):
            return np.zeros(image.shape[:2], dtype=np.uint8)

    analyzer = SceneAnalyzer(_FakeDetector(), _PlainSegmenter(), depth=None)
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    floor_mask = np.full((100, 100), 255, dtype=np.uint8)

    result, table_boxes, protected_mask = analyzer._carve_obstructions(image, floor_mask)
    assert result is floor_mask
    assert table_boxes == []
    assert not protected_mask.any()


def test_obstruction_carve_skipped_without_detections():
    class _NoFurnitureDetector(_FakeDetector):
        def detect(self, image, prompt):
            if prompt == "floor":
                return [Detection(label="floor", score=1.0, box=(0, 0, 300, 300))]
            return []

    analyzer = SceneAnalyzer(_NoFurnitureDetector(), _FakeSegmenter(), depth=None)
    image = np.zeros((300, 300, 3), dtype=np.uint8)
    floor_mask = np.full((300, 300), 255, dtype=np.uint8)

    result, table_boxes, protected_mask = analyzer._carve_obstructions(image, floor_mask)
    assert result is floor_mask
    assert table_boxes == []
    assert not protected_mask.any()


def test_reclaim_under_tables_restores_on_plane_floor():
    h, w = 200, 200
    ys, xs = np.mgrid[0:h, 0:w]
    depth = (
        0.5
        + 0.001 * xs
        + 0.001 * ys
        + 0.00003 * (xs - 100) ** 2
        + 0.00003 * (ys - 100) ** 2
    ).astype(np.float32)
    floor = np.full((h, w), 255, dtype=np.uint8)
    plane = PlaneEstimator(seed=1).estimate(floor, depth)

    carved = floor.copy()
    carved[50:150, 50:150] = 0

    result = SceneAnalyzer._reclaim_under_tables(
        carved, depth, plane, [(50, 50, 150, 150)]
    )

    assert (result[50:150, 50:150] == 255).all()


def test_reclaim_under_tables_keeps_off_plane_object():
    h, w = 200, 200
    ys, xs = np.mgrid[0:h, 0:w]
    depth = (0.5 + 0.001 * xs + 0.001 * ys).astype(np.float32)
    floor = np.full((h, w), 255, dtype=np.uint8)
    plane = PlaneEstimator(seed=1).estimate(floor, depth)

    carved = floor.copy()
    carved[50:150, 50:150] = 0
    raised = depth.copy()
    raised[50:150, 50:150] += 0.5

    result = SceneAnalyzer._reclaim_under_tables(
        carved, raised, plane, [(50, 50, 150, 150)]
    )

    assert (result[50:150, 50:150] == 0).all()
    assert (result[:50, :] > 0).all()
