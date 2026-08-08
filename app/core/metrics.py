"""Small dependency-free metrics for APEX Vision AI runtime diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass(slots=True)
class RenderMetrics:
    """Thread-safe counters and timing aggregates for render jobs."""

    _lock: Lock = field(default_factory=Lock, repr=False)
    jobs_started: int = 0
    jobs_completed: int = 0
    jobs_failed: int = 0
    jobs_superseded: int = 0
    total_duration_seconds: float = 0.0

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

    def snapshot(self) -> dict[str, float | int]:
        with self._lock:
            completed = self.jobs_completed + self.jobs_failed
            return {
                "jobs_started": self.jobs_started,
                "jobs_completed": self.jobs_completed,
                "jobs_failed": self.jobs_failed,
                "jobs_superseded": self.jobs_superseded,
                "total_duration_seconds": round(self.total_duration_seconds, 4),
                "average_duration_seconds": round(
                    self.total_duration_seconds / completed, 4
                ) if completed else 0.0,
            }


render_metrics = RenderMetrics()
