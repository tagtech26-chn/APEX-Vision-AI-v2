"""Evaluation utilities for material/finish classifier benchmarks.

The evaluator is intentionally model-agnostic. It consumes predictions and
labelled ground truth records and reports measurable classification quality;
it does not invent an accuracy claim when no labelled dataset is available.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MaterialBenchmarkCase:
    """A single labelled evaluation example."""

    expected_material: str
    predicted_material: str
    expected_finish: str | None = None
    predicted_finish: str | None = None


@dataclass(frozen=True)
class ClassificationMetrics:
    """Aggregate classification metrics for one label dimension."""

    samples: int
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    labels: tuple[str, ...]
    confusion_matrix: tuple[tuple[int, ...], ...]


def _metrics(
    expected: list[str],
    predicted: list[str],
) -> ClassificationMetrics:
    if len(expected) != len(predicted):
        raise ValueError("Expected and predicted labels must have equal length")
    if not expected:
        raise ValueError("At least one labelled example is required")

    labels = tuple(sorted(set(expected) | set(predicted)))
    index = {label: i for i, label in enumerate(labels)}
    matrix = [[0 for _ in labels] for _ in labels]
    for actual, guess in zip(expected, predicted):
        matrix[index[actual]][index[guess]] += 1

    precisions: list[float] = []
    recalls: list[float] = []
    f1s: list[float] = []
    for i in range(len(labels)):
        tp = matrix[i][i]
        predicted_total = sum(row[i] for row in matrix)
        actual_total = sum(matrix[i])
        precision = tp / predicted_total if predicted_total else 0.0
        recall = tp / actual_total if actual_total else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

    return ClassificationMetrics(
        samples=len(expected),
        accuracy=sum(a == p for a, p in zip(expected, predicted)) / len(expected),
        macro_precision=sum(precisions) / len(labels),
        macro_recall=sum(recalls) / len(labels),
        macro_f1=sum(f1s) / len(labels),
        labels=labels,
        confusion_matrix=tuple(tuple(row) for row in matrix),
    )


def evaluate_material_benchmark(
    cases: Iterable[MaterialBenchmarkCase],
) -> dict[str, ClassificationMetrics]:
    """Evaluate material and, when supplied, finish labels independently."""
    records = list(cases)
    if not records:
        raise ValueError("At least one benchmark case is required")

    material = _metrics(
        [case.expected_material for case in records],
        [case.predicted_material for case in records],
    )
    result = {"material": material}

    finish_records = [
        case
        for case in records
        if case.expected_finish is not None and case.predicted_finish is not None
    ]
    if finish_records:
        result["finish"] = _metrics(
            [case.expected_finish for case in finish_records],
            [case.predicted_finish for case in finish_records],
        )

    return result


def benchmark_summary(metrics: dict[str, ClassificationMetrics]) -> dict[str, object]:
    """Return JSON-safe benchmark output suitable for CI artifacts/logging."""
    return {
        dimension: {
            "samples": value.samples,
            "accuracy": round(value.accuracy, 6),
            "macro_precision": round(value.macro_precision, 6),
            "macro_recall": round(value.macro_recall, 6),
            "macro_f1": round(value.macro_f1, 6),
            "labels": list(value.labels),
            "confusion_matrix": [list(row) for row in value.confusion_matrix],
        }
        for dimension, value in metrics.items()
    }
