import pytest

from app.ai.material.benchmark import (
    MaterialBenchmarkCase,
    benchmark_summary,
    evaluate_material_benchmark,
)


def test_material_benchmark_reports_accuracy_precision_recall_and_f1() -> None:
    cases = [
        MaterialBenchmarkCase("ceramic", "ceramic", "gloss", "gloss"),
        MaterialBenchmarkCase("ceramic", "stone", "matte", "matte"),
        MaterialBenchmarkCase("stone", "stone", "matte", "gloss"),
        MaterialBenchmarkCase("wood", "wood", "satin", "satin"),
    ]

    metrics = evaluate_material_benchmark(cases)

    assert metrics["material"].samples == 4
    assert metrics["material"].accuracy == pytest.approx(0.75)
    assert metrics["material"].labels == ("ceramic", "stone", "wood")
    assert metrics["material"].confusion_matrix == (
        (1, 1, 0),
        (0, 1, 0),
        (0, 0, 1),
    )
    assert 0.0 <= metrics["material"].macro_f1 <= 1.0
    assert 0.0 <= metrics["finish"].macro_f1 <= 1.0


def test_benchmark_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="At least one"):
        evaluate_material_benchmark([])


def test_benchmark_summary_is_json_safe() -> None:
    cases = [MaterialBenchmarkCase("ceramic", "ceramic")]
    summary = benchmark_summary(evaluate_material_benchmark(cases))

    assert summary["material"]["accuracy"] == 1.0
    assert summary["material"]["labels"] == ["ceramic"]
    assert summary["material"]["confusion_matrix"] == [[1]]
    assert "finish" not in summary
