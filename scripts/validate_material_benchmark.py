"""Validate the versioned material benchmark contract for CI.

This gate validates dataset integrity and provenance metadata. It intentionally
does not turn a synthetic CI fixture into a production accuracy claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "benchmarks" / "materials" / "v1" / "benchmark.json"
MATERIALS = {"ceramic", "stone", "wood", "vinyl", "carpet"}
FINISHES = {"matte", "satin", "gloss"}
SPLITS = {"train", "validation", "test"}


def validate(path: Path, require_production: bool = False) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"dataset", "version", "status", "records"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"Missing benchmark fields: {sorted(missing)}")

    if require_production and payload["status"] != "production":
        raise ValueError("Production accuracy gate requires a production-labelled dataset")

    records = payload["records"]
    if not isinstance(records, list) or not records:
        raise ValueError("Benchmark must contain at least one record")

    ids: set[str] = set()
    for record in records:
        for field in ("id", "material", "finish", "split", "source"):
            if not record.get(field):
                raise ValueError(f"Benchmark record missing required field: {field}")
        if record["id"] in ids:
            raise ValueError(f"Duplicate benchmark id: {record['id']}")
        ids.add(record["id"])
        if record["material"] not in MATERIALS:
            raise ValueError(f"Unsupported material: {record['material']}")
        if record["finish"] not in FINISHES:
            raise ValueError(f"Unsupported finish: {record['finish']}")
        if record["split"] not in SPLITS:
            raise ValueError(f"Unsupported split: {record['split']}")

    return {
        "dataset": payload["dataset"],
        "version": payload["version"],
        "status": payload["status"],
        "samples": len(records),
        "splits": sorted({record["split"] for record in records}),
        "production_accuracy_gate": payload["status"] == "production",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--require-production", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    summary = validate(args.manifest, args.require_production)
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
