from __future__ import annotations

from app.ai.scene.analyzer import build_scene_analyzer
from app.ai.scene.v22 import V22SceneAnalyzer


def test_v22_provider_factory_returns_v22_analyzer() -> None:
    analyzer = build_scene_analyzer("v22")

    assert isinstance(analyzer, V22SceneAnalyzer)
    assert set(analyzer.providers) == {"detector", "segmenter", "depth"}


def test_v22_provider_is_registered() -> None:
    from app.ai.config import VALID_PROVIDERS, resolve_provider

    assert "v22" in VALID_PROVIDERS
    assert resolve_provider("V22") == "v22"
