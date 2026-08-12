from __future__ import annotations

import numpy as np

from app.ai.geometry.metric_floor import MetricFloorEstimator
from app.ai.scene.v22._analyzer import V22SceneAnalyzer


def test_metric_floor_plane_is_stable_on_synthetic_ground() -> None:
    h, w = 120, 160
    yy, xx = np.mgrid[0:h, 0:w]
    depth = (1.0 + 0.003 * yy + 0.0002 * xx).astype(np.float32)
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[55:, 10:-10] = 255

    estimator = MetricFloorEstimator(sample_size=5000)
    result = estimator.estimate(mask, depth)

    assert np.isfinite(result.normal).all()
    assert np.isfinite(result.equation).all()
    assert 0.0 <= result.inlier_ratio <= 1.0
    assert result.residual_p95 < 0.08


def test_v22_refinement_never_expands_beyond_semantic_floor() -> None:
    seed = np.zeros((100, 140), dtype=np.uint8)
    seed[50:, 10:130] = 255
    residual = np.zeros((100, 140), dtype=np.float32)
    protected = np.zeros_like(seed)
    protected[70:82, 55:75] = 255

    refined = V22SceneAnalyzer._refine_floor_mask(
        seed,
        residual,
        normals=None,
        residual_threshold=0.05,
        protected=protected,
    )

    assert not np.any((refined > 0) & (seed == 0))
    assert not np.any(refined[70:82, 55:75] > 0)
    assert int((refined > 0).sum()) > 0
