"""Room listing endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import services

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])


@router.get("")
def get_rooms():
    return services.rooms.list_rooms()
