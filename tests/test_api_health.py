from fastapi.testclient import TestClient

from app.ai.config import heavy_models_available
from app.main import app


client = TestClient(app, base_url="http://127.0.0.1")


def test_health_contract() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"success": True, "status": "ok", "version": "2.1.0"}


def test_readiness_contract() -> None:
    response = client.get("/api/ready")
    body = response.json()

    # CI/dev environments intentionally do not carry the multi-GB heavy model
    # weights. In that case readiness must fail explicitly instead of pretending
    # the heavy provider is ready. A fully provisioned environment must return
    # the normal 200/ready contract.
    available, _ = heavy_models_available()
    if available and response.status_code == 200:
        assert body["status"] == "ready"
        return

    assert response.status_code == 503
    assert body["status"] in {"not_ready", "warming_up"}
    assert body["success"] is False


def test_diagnostics_does_not_expose_model_paths() -> None:
    response = client.get("/api/diagnostics")
    assert response.status_code == 200
    body = response.json()
    assert body["application"] == "APEX Vision AI"
    assert "grounding_dino_ckpt" not in str(body)
    assert "sam2_ckpt" not in str(body)
