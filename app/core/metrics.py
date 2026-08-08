"""Dependency-free runtime metrics for APEX Vision AI diagnostics and performance."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass(slots=True)
class RenderMetrics:
    """Thread-safe counters and timing aggregates for render jobs and cache use."""

    _lock: Lock = field(default_factory=Lock, repr=False)
    jobs_started: int = 0
    jobs_completed: int = 0
    jobs_failed: int = 0
    jobs_superseded: int = 0
    total_duration_seconds: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_errors: int = 0
    stage_totals: dict[str, float] = field(default_factory=dict)
    stage_counts: dict[str, int] = field(default_factory=dict)

    def started(self) -> None:
        with self._lock:
            self.jobs_started += 1

    def finished(self, duration_seconds: float) -> None:
        with self._lock:
            self.jobs_completed += 1
            self.total_duration_seconds += max(0.0, duration_seconds)

    def failed(self, duration_seconds: float) -> None:
        with self._lock:
            self.jobs_failed += 1
            self.total_duration_seconds += max(0.0, duration_seconds)

    def superseded(self) -> None:
        with self._lock:
            self.jobs_superseded += 1

    def cache_hit(self) -> None:
        with self._lock:
            self.cache_hits += 1

    def cache_miss(self) -> None:
        with self._lock:
            self.cache_misses += 1

    def cache_error(self) -> None:
        with self._lock:
            self.cache_errors += 1

    def stage(self, name: str, duration_seconds: float) -> None:
        with self._lock:
            self.stage_totals[name] = self.stage_totals.get(name, 0.0) + max(0.0, duration_seconds)
            self.stage_counts[name] = self.stage_counts.get(name, 0) + 1

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            completed = self.jobs_completed + self.jobs_failed
            stage_averages = {
                name: round(total / self.stage_counts[name], 4)
                for name, total in self.stage_totals.items()
                if self.stage_counts.get(name, 0)
            }
            return {
                "jobs_started": self.jobs_started,
                "jobs_completed": self.jobs_completed,
                "jobs_failed": self.jobs_failed,
                "jobs_superseded": self.jobs_superseded,
                "total_duration_seconds": round(self.total_duration_seconds, 4),
                "average_duration_seconds": round(self.total_duration_seconds / completed, 4) if completed else 0.0,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_errors": self.cache_errors,
                "stage_average_seconds": stage_averages,
            }


render_metrics = RenderMetrics()
