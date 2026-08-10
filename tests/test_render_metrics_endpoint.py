from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app, base_url="http://127.0.0.1")


def test_render_metrics_endpoint_is_reachable() -> None:
    response = client.get("/api/render/metrics")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "jobs_started" in body["metrics"]
    assert "cache_hits" in body["metrics"]
