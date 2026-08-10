import numpy as np

from app.renderer.mask_feather import MaskFeather


def test_feather_never_bleeds_outside_mask() -> None:
    mask = np.zeros((21, 21), dtype=np.uint8)
    mask[5:16, 5:16] = 255

    alpha = MaskFeather().feather(mask, radius=3)

    assert alpha.shape == mask.shape
    assert alpha.dtype == np.float32
    assert np.all(alpha[mask == 0] == 0.0)
    assert alpha[10, 10] == 1.0
    assert 0.0 < alpha[5, 10] < 1.0


def test_zero_radius_returns_binary_alpha() -> None:
    mask = np.zeros((5, 5), dtype=np.uint8)
    mask[1:4, 1:4] = 255

    alpha = MaskFeather().feather(mask, radius=0)

    assert np.array_equal(alpha, (mask > 0).astype(np.float32))


def test_empty_mask_returns_zero_alpha() -> None:
    mask = np.zeros((8, 8), dtype=np.uint8)

    alpha = MaskFeather().feather(mask, radius=5)

    assert np.count_nonzero(alpha) == 0
