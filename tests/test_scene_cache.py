from pathlib import Path

import pytest

from app.cache.scene_cache import SceneCache


def test_cache_is_disabled_without_signing_key(tmp_path: Path) -> None:
    cache = SceneCache(tmp_path, signing_key="")
    assert cache.enabled is False
    assert cache.exists("room") is False
    with pytest.raises(FileNotFoundError):
        cache.load("room")


def test_cache_rejects_relative_names(tmp_path: Path) -> None:
    cache = SceneCache(tmp_path, signing_key="test-secret")
    with pytest.raises(ValueError):
        cache._path("../room")
