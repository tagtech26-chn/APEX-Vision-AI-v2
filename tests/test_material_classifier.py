import numpy as np
import pytest

from app.ai.material.classifier import classify_surface


def test_material_classifier_is_deterministic() -> None:
    image = np.zeros((128, 128, 3), dtype=np.uint8)
    image[:, ::8] = 220

    first = classify_surface(image)
    second = classify_surface(image)

    assert first == second
    assert first["material"] in {"ceramic", "stone", "wood", "vinyl", "carpet"}
    assert first["finish"] in {"matte", "satin", "gloss"}
    assert 0.0 <= first["confidence"] <= 1.0
    assert 1.0 <= first["texture_scale_factor"] <= 2.0
    assert first["method"] == "deterministic-baseline-v2"


def test_material_classifier_rejects_invalid_images() -> None:
    with pytest.raises(ValueError):
        classify_surface(np.empty((0, 0), dtype=np.uint8))

    with pytest.raises(ValueError):
        classify_surface(np.zeros((4, 4), dtype=np.uint8))


def test_material_classifier_reports_texture_and_finish_features() -> None:
    image = np.random.default_rng(7).integers(0, 256, (64, 96), dtype=np.uint8)

    result = classify_surface(image)

    assert set(result["features"]) == {
        "texture_variance",
        "edge_density",
        "periodicity",
        "highlight_ratio",
        "local_contrast",
    }


def test_material_classifier_finish_is_stable_for_uniform_surface() -> None:
    image = np.full((64, 64), 120, dtype=np.uint8)
    result = classify_surface(image)

    assert result["finish"] == "matte"
    assert result["features"]["highlight_ratio"] == 0.0
