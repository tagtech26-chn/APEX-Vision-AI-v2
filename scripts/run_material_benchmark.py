"""Run the material benchmark from labelled records and classifier predictions.

The runner never generates predictions. Predictions must be supplied by the
actual classifier/model under evaluation, keeping benchmark results auditable.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.ai.material.benchmark import MaterialBenchmarkCase, benchmark_summary, evaluate_material_benchmark
from scripts.validate_material_benchmark import validate

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "benchmarks" / "materials" / "v1" / "benchmark.json"


def run(manifest_path: Path, predictions_path: Path, require_production: bool = False) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate(manifest_path, require_production=require_production)
    predictions = json.loads(predictions_path.read_text(encoding="utf-8"))
    if not isinstance(predictions, list):
        raise ValueError("Predictions must be a JSON list")

    by_id = {}
    for prediction in predictions:
        if not prediction.get("id"):
            raise ValueError("Prediction missing id")
        if prediction["id"] in by_id:
            raise ValueError(f"Duplicate prediction id: {prediction['id']}")
        by_id[prediction["id"]] = prediction

    test_records = [record for record in manifest["records"] if record["split"] == "test"]
    missing = [record["id"] for record in test_records if record["id"] not in by_id]
    extra = sorted(set(by_id) - {record["id"] for record in test_records})
    if missing:
        raise ValueError(f"Missing predictions for test records: {missing}")
    if extra:
        raise ValueError(f"Predictions contain non-test or unknown ids: {extra}")

    cases = []
    for record in test_records:
        prediction = by_id[record["id"]]
        cases.append(
            MaterialBenchmarkCase(
                expected_material=record["material"],
                predicted_material=prediction.get("material"),
                expected_finish=record.get("finish"),
                predicted_finish=prediction.get("finish"),
            )
        )

    metrics = evaluate_material_benchmark(cases)
    return {
        "dataset": manifest["dataset"],
        "version": manifest["version"],
        "status": manifest["status"],
        "test_samples": len(test_records),
        "metrics": benchmark_summary(metrics),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--require-production", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    summary = run(args.manifest, args.predictions, args.require_production)
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
