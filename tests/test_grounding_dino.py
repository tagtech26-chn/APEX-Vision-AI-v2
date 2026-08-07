"""Tests for GroundingDINO box handling (no model download required)."""

from __future__ import annotations

import numpy as np

from app.ai.detection.base import Detection


def test_normalised_box_converts_to_pixels():
    """GroundingDINO returns cxcywh in [0, 1]; scale to pixel xyxy.

    The old code truncated normalised coordinates with int(), collapsing every
    box to (0, 0, 0, 0).
    """
    w, h = 1413, 970
    box = np.array([0.4999, 0.7698, 0.9977, 0.4583])  # normalised cxcywh
    cx, cy, bw, bh = box * np.array([w, h, w, h])
    x1, y1 = int(cx - bw / 2), int(cy - bh / 2)
    x2, y2 = int(cx + bw / 2), int(cy + bh / 2)

    assert x1 >= 0 and y1 >= 0
    assert x2 > x1 and y2 > y1
    assert x2 <= w and y2 <= h
    assert (x2 - x1) > 0.9 * w  # full-width floor box


def test_detection_accepts_pixel_box():
    detection = Detection(label="floor", score=0.87, box=(0, 525, 1411, 969))
    x1, y1, x2, y2 = detection.box
    assert x2 > x1 and y2 > y1
