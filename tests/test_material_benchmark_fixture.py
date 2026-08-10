import json
from pathlib import Path


FIXTURE = Path(__file__).parents[1] / "data" / "benchmarks" / "materials" / "v1" / "benchmark.json"
ALLOWED_MATERIALS = {"ceramic", "stone", "wood", "vinyl", "carpet"}
ALLOWED_FINISHES = {"matte", "satin", "gloss"}


def test_material_benchmark_fixture_is_versioned_and_well_formed() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert payload["dataset"] == "apex-vision-ai-materials"
    assert payload["version"] == "1.0.0"
    assert payload["status"] == "ci-fixture"
    assert len(payload["records"]) >= 5

    ids = set()
    for record in payload["records"]:
        assert record["id"] not in ids
        ids.add(record["id"])
        assert record["material"] in ALLOWED_MATERIALS
        assert record["finish"] in ALLOWED_FINISHES
        assert record["split"] in {"train", "validation", "test"}
        assert record["source"]


def test_ci_fixture_does_not_claim_real_image_evidence() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["status"] == "ci-fixture"
    assert all(record["image"] is None for record in payload["records"])
