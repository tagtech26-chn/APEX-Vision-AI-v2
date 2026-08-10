from app.core.metrics import RenderMetrics


def test_render_metrics_snapshot_tracks_jobs_and_cache() -> None:
    metrics = RenderMetrics()
    metrics.started()
    metrics.finished(1.25)
    metrics.started()
    metrics.failed(0.75)
    metrics.superseded()
    metrics.cache_hit()
    metrics.cache_miss()
    metrics.cache_error()

    assert metrics.snapshot() == {
        "jobs_started": 2,
        "jobs_completed": 1,
        "jobs_failed": 1,
        "jobs_superseded": 1,
        "total_duration_seconds": 2.0,
        "average_duration_seconds": 1.0,
        "cache_hits": 1,
        "cache_misses": 1,
        "cache_errors": 1,
        "stage_average_seconds": {},
    }


def test_render_metrics_snapshot_tracks_stage_averages() -> None:
    metrics = RenderMetrics()
    metrics.stage("tile_load", 0.2)
    metrics.stage("tile_load", 0.4)
    metrics.stage("render", 1.0)

    snapshot = metrics.snapshot()

    assert snapshot["stage_average_seconds"] == {
        "tile_load": 0.3,
        "render": 1.0,
    }
