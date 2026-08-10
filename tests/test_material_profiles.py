import numpy as np

from app.renderer.material_engine import MATERIAL_PROFILES, MaterialEngine


def test_all_material_profiles_are_supported() -> None:
    engine = MaterialEngine()
    image = np.full((32, 32, 3), 128, dtype=np.uint8)

    for profile in MATERIAL_PROFILES:
        result = engine.enhance(image, profile=profile)
        assert result.shape == image.shape
        assert result.dtype == np.uint8
        assert np.isfinite(result).all()
        assert result.min() >= 0
        assert result.max() <= 255


def test_unknown_profile_falls_back_to_generic() -> None:
    engine = MaterialEngine()
    image = np.full((16, 16, 3), 128, dtype=np.uint8)

    generic = engine.enhance(image, profile="generic")
    unknown = engine.enhance(image, profile="not-a-real-profile")

    assert np.array_equal(generic, unknown)


def test_material_profiles_are_not_mutated_during_rendering() -> None:
    before = {name: values.copy() for name, values in MATERIAL_PROFILES.items()}
    image = np.arange(32 * 32 * 3, dtype=np.uint8).reshape(32, 32, 3)
    MaterialEngine().enhance(image, profile="wood")
    assert MATERIAL_PROFILES == before
