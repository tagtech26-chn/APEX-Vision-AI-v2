import json
from pathlib import Path

import pytest

from scripts.run_material_benchmark import run


ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "data" / "benchmarks" / "materials" / "v1" / "benchmark.json"


def write_predictions(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {"id": "fixture-ceramic-gloss-001", "material": "ceramic", "finish": "gloss"},
                {"id": "fixture-stone-matte-001", "material": "stone", "finish": "matte"},
                {"id": "fixture-wood-satin-001", "material": "wood", "finish": "satin"},
                {"id": "fixture-vinyl-matte-001", "material": "vinyl", "finish": "matte"},
                {"id": "fixture-carpet-matte-001", "material": "carpet", "finish": "matte"},
            ]
        ),
        encoding="utf-8",
    )


def test_runner_evaluates_classifier_predictions(tmp_path: Path) -> None:
    predictions = tmp_path / "predictions.json"
    write_predictions(predictions)

    summary = run(MANIFEST, predictions)

    assert summary["status"] == "ci-fixture"
    assert summary["test_samples"] == 5
    assert summary["metrics"]["material"]["accuracy"] == 1.0
    assert summary["metrics"]["finish"]["accuracy"] == 1.0


def test_runner_requires_complete_test_predictions(tmp_path: Path) -> None:
    predictions = tmp_path / "predictions.json"
    predictions.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing predictions"):
        run(MANIFEST, predictions)
