"""Evaluate measured material benchmark metrics against production thresholds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(manifest: dict[str, object], metrics: dict[str, object], gate: dict[str, object]) -> dict[str, object]:
    activation = gate["activation"]
    if manifest.get("status") != activation["required_dataset_status"]:
        raise ValueError("Production quality gate requires a production-labelled dataset")
    if manifest.get("dataset") != gate["dataset"]:
        raise ValueError("Benchmark dataset does not match the quality gate")

    records = manifest.get("records", [])
    test_count = sum(record.get("split") == activation["required_split"] for record in records)
    if test_count < max(gate["minimum_samples"], activation["min_test_samples"]):
        raise ValueError("Production benchmark does not contain enough held-out test samples")

    failures: list[str] = []
    measured = metrics.get("metrics", {})
    for dimension, thresholds in gate["metrics"].items():
        actual = measured.get(dimension)
        if not actual:
            failures.append(f"missing metrics: {dimension}")
            continue
        for metric, minimum in thresholds.items():
            value = actual.get(metric)
            if value is None:
                failures.append(f"missing metric: {dimension}.{metric}")
            elif value < minimum:
                failures.append(f"{dimension}.{metric}={value:.6f} < {minimum:.6f}")

    return {
        "passed": not failures,
        "dataset": manifest["dataset"],
        "dataset_version": manifest["version"],
        "test_samples": test_count,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = evaluate(load(args.manifest), load(args.metrics), load(args.gate))
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
