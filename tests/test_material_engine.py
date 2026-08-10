import numpy as np

from app.renderer.material_engine import MaterialEngine


def test_finish_profiles_produce_deterministic_outputs() -> None:
    engine = MaterialEngine()
    projection = np.full((64, 64, 3), 180, dtype=np.uint8)

    matte = engine.enhance(projection, profile="ceramic", finish="matte")
    satin = engine.enhance(projection, profile="ceramic", finish="satin")
    gloss = engine.enhance(projection, profile="ceramic", finish="gloss")

    assert matte.shape == projection.shape
    assert satin.shape == projection.shape
    assert gloss.shape == projection.shape
    assert matte.dtype == np.uint8
    assert np.array_equal(matte, engine.enhance(projection, profile="ceramic", finish="matte"))


def test_texture_scale_factor_is_bounded() -> None:
    engine = MaterialEngine()
    projection = np.random.default_rng(3).integers(0, 256, (32, 32, 3), dtype=np.uint8)

    low = engine.enhance(projection, profile="wood", texture_scale_factor=0.1)
    high = engine.enhance(projection, profile="wood", texture_scale_factor=9.0)

    assert low.shape == high.shape == projection.shape
    assert low.dtype == high.dtype == np.uint8
