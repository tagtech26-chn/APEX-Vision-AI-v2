import json
from pathlib import Path

import pytest

from scripts.evaluate_material_quality_gate import evaluate, load

ROOT = Path(__file__).parents[1]
MANIFEST = load(ROOT / "data/benchmarks/materials/v1/benchmark.json")
GATE = load(ROOT / "data/benchmarks/materials/v1/quality-gate.json")


def production_manifest() -> dict:
    payload = json.loads(json.dumps(MANIFEST))
    payload["status"] = "production"
    payload["records"] = [
        {
            "id": f"test-{i}",
            "image": f"images/{i}.jpg",
            "material": "ceramic",
            "finish": "gloss",
            "split": "test",
            "source": "approved-labelled-dataset",
        }
        for i in range(100)
    ]
    return payload


def test_production_gate_passes_when_thresholds_are_met() -> None:
    result = evaluate(
        production_manifest(),
        {"metrics": {"material": {"accuracy": 0.95, "macro_f1": 0.94}, "finish": {"accuracy": 0.90, "macro_f1": 0.89}}},
        GATE,
    )
    assert result["passed"] is True
    assert result["failures"] == []


def test_production_gate_reports_threshold_failures() -> None:
    result = evaluate(
        production_manifest(),
        {"metrics": {"material": {"accuracy": 0.80, "macro_f1": 0.90}, "finish": {"accuracy": 0.85, "macro_f1": 0.85}}},
        GATE,
    )
    assert result["passed"] is False
    assert "material.accuracy=0.800000 < 0.900000" in result["failures"]


def test_ci_fixture_cannot_activate_production_gate() -> None:
    with pytest.raises(ValueError, match="production-labelled dataset"):
        evaluate(MANIFEST, {"metrics": {}}, GATE)
