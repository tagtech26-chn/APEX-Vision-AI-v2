from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_contract() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"success": True, "status": "ok", "version": "2.1.0"}


def test_readiness_contract() -> None:
    response = client.get("/api/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_diagnostics_does_not_expose_model_paths() -> None:
    response = client.get("/api/diagnostics")
    assert response.status_code == 200
    body = response.json()
    assert body["application"] == "APEX Vision AI"
    assert "grounding_dino_ckpt" not in str(body)
    assert "sam2_ckpt" not in str(body)
