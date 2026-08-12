from __future__ import annotations

import numpy as np

from app.ai.geometry.advisor import GeminiGeometryAdvisor, apply_advisor_protection, build_geometry_advisor


def test_geometry_advisor_defaults_to_disabled_without_key(monkeypatch) -> None:
    monkeypatch.delenv("APEX_GEOMETRY_ADVISOR", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    advisor = build_geometry_advisor()

    assert advisor.name == "none"
    assert advisor.advise(np.zeros((10, 10, 3), dtype=np.uint8), np.ones((10, 10), dtype=np.uint8), np.zeros((4, 2))) == {
        "enabled": False,
        "provider": "none",
    }


def test_gemini_advisor_reports_missing_key_without_network(monkeypatch) -> None:
    monkeypatch.setenv("APEX_GEOMETRY_ADVISOR", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    advisor = build_geometry_advisor()
    result = advisor.advise(np.zeros((10, 10, 3), dtype=np.uint8), np.ones((10, 10), dtype=np.uint8), np.zeros((4, 2)))

    assert result["provider"] == "gemini"
    assert result["enabled"] is False
    assert result["status"] == "missing_api_key"


def test_advisor_never_expands_floor_and_requires_confidence() -> None:
    floor = np.zeros((20, 30), dtype=np.uint8)
    floor[5:18, 5:25] = 255
    advice = {
        "enabled": True,
        "provider": "gemini",
        "status": "ok",
        "confidence": 0.9,
        "protected_boxes": [[10, 8, 20, 14]],
    }

    refined, protected, pixels = apply_advisor_protection(floor, advice)

    assert not np.any((refined > 0) & (floor == 0))
    assert pixels > 0
    assert np.any(protected > 0)
    assert not np.any(refined[8:14, 10:20] > 0)


def test_advisor_low_confidence_is_informational_only() -> None:
    floor = np.ones((20, 20), dtype=np.uint8) * 255
    advice = {
        "enabled": True,
        "provider": "gemini",
        "status": "ok",
        "confidence": 0.5,
        "protected_boxes": [[2, 2, 18, 18]],
    }

    refined, protected, pixels = apply_advisor_protection(floor, advice)

    assert np.array_equal(refined, floor)
    assert not np.any(protected)
    assert pixels == 0
