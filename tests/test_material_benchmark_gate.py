from pathlib import Path

import pytest

from scripts.validate_material_benchmark import validate


MANIFEST = Path(__file__).parents[1] / "data" / "benchmarks" / "materials" / "v1" / "benchmark.json"


def test_ci_fixture_passes_contract_gate() -> None:
    summary = validate(MANIFEST)

    assert summary["dataset"] == "apex-vision-ai-materials"
    assert summary["version"] == "1.0.0"
    assert summary["status"] == "ci-fixture"
    assert summary["samples"] == 5
    assert summary["production_accuracy_gate"] is False


def test_ci_fixture_cannot_be_used_as_production_accuracy_evidence() -> None:
    with pytest.raises(ValueError, match="production-labelled dataset"):
        validate(MANIFEST, require_production=True)
