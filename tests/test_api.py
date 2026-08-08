"""API integration tests via FastAPI TestClient."""

from __future__ import annotations

import os
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    # Isolate output/scenes so tests don't pollute the real assets.
    temp = tmp_path_factory.mktemp("apex_api")
    os.environ["APEX_OUTPUT"] = str(temp / "output")
    os.environ["APEX_SCENES"] = str(temp / "scenes")

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_home(client):
    # When the built frontend exists, "/" serves the SPA; otherwise the legacy JSON home.
    response = client.get("/")
    assert response.status_code == 200
    if "text/html" in response.headers.get("content-type", ""):
        assert response.text.lstrip().lower().startswith("<!doctype html>")
    else:
        data = response.json()
        assert data["status"] == "Running"
        assert data["version"] == "2.1.0"


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_rooms_endpoint(client):
    response = client.get("/api/rooms")
    assert response.status_code == 200
    rooms = response.json()
    assert isinstance(rooms, list)
    assert all("id" in room and "name" in room for room in rooms)


def test_catalog_endpoints(client):
    tiles = client.get("/api/catalog/tiles").json()
    assert isinstance(tiles, list)
    assert len(tiles) >= 3

    categories = client.get("/api/catalog/categories").json()
    assert isinstance(categories, list)

    sizes = client.get("/api/catalog/sizes").json()
    assert isinstance(sizes, list)


def test_render_endpoint_invalid_room(client):
    response = client.post("/api/render", json={"room": 9999, "tile": 1})
    assert response.status_code == 404


def test_render_endpoint_invalid_pattern(client):
    response = client.post(
        "/api/render",
        json={"room": 1, "tile": 1, "pattern": "Wonky"},
    )
    assert response.status_code == 422


class _StubAnalyzer:
    """Minimal analyzer stub so the happy-path test doesn't need real AI models."""

    providers = {"detector": "stub", "segmenter": "stub", "depth": "stub"}

    def analyze(self, room_path, progress_cb=None):
        from app.ai.scene.result import SceneResult

        image = np.zeros((200, 300, 3), dtype=np.uint8)
        mask = np.zeros((200, 300), dtype=np.uint8)
        mask[100:, 40:260] = 255
        return SceneResult(
            image=image,
            width=300,
            height=200,
            floor_mask=mask,
            floor_polygon=np.array(
                [[60, 100], [240, 100], [280, 199], [20, 199]], dtype=np.float32
            ),
            homography=np.eye(3, dtype=np.float32),
        )


def test_render_job_happy_path(
    client, monkeypatch, room_image_path, tile_image_path, tmp_path
):
    """A submitted render job should poll through to status 'done'."""
    from app.api.deps import services as api_services
    from app.cache.scene_cache import SceneCache
    from app.services.render_service import RenderService

    # Swap in a stub analyzer + isolated cache so this test is fast,
    # deterministic, and doesn't depend on real committed room/tile assets.
    monkeypatch.setattr(
        api_services,
        "_render",
        RenderService(analyzer=_StubAnalyzer(), cache=SceneCache(root=tmp_path / "scenes")),
    )
    monkeypatch.setattr(api_services.rooms, "get_room", lambda room_id: room_image_path)
    monkeypatch.setattr(
        api_services.tiles,
        "get_tile",
        lambda tile_id: {"image_path": str(tile_image_path)},
    )

    response = client.post("/api/render", json={"room": 1, "tile": 1})
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    assert response.json()["status"] == "queued"

    deadline = time.time() + 5
    job = client.get(f"/api/render/{job_id}").json()
    while job["status"] in ("queued", "processing") and time.time() < deadline:
        time.sleep(0.05)
        job = client.get(f"/api/render/{job_id}").json()

    assert job["status"] == "done", job
    assert job["image"].startswith("/output/")
    assert job["filename"]
