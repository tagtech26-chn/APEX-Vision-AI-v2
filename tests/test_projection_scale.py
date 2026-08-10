import pytest

from app.renderer.projection_scale import evaluate_projection_scale


def test_projection_scale_matches_physical_tile_size() -> None:
    scale = evaluate_projection_scale(tile_size_mm=600, tile_pixels=157)

    assert scale.estimated_tiles_across == pytest.approx(13.0)
    assert scale.pixels_per_mm == pytest.approx(157 / 600)
    assert scale.as_dict()["tile_size_mm"] == 600


def test_projection_scale_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError):
        evaluate_projection_scale(0, 100)
    with pytest.raises(ValueError):
        evaluate_projection_scale(600, 0)
    with pytest.raises(ValueError):
        evaluate_projection_scale(600, 100, plane_span_pixels=0)
