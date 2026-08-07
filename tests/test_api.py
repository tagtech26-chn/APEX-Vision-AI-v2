"""API integration tests via FastAPI TestClient."""

from __future__ import annotations

import os

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
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Running"
    assert data["version"] == "2.0.0"


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
