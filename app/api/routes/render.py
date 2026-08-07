"""Render endpoint: job-based so slow first-time AI analysis doesn't hang.

Stale renders for the same room are superseded so rapid tile changes never
show an outdated result: only the latest submitted job for a room may report
"done"; superseded jobs report "superseded" and are skipped by the frontend.
"""

from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.api.deps import services
from app.api.schemas import RenderRequest

logger = logging.getLogger("apex.api")

router = APIRouter(prefix="/api/render", tags=["Render"])

# One worker: the heavy AI stack (models + analysis) is single-threaded and
# serialising jobs keeps predictions safe.
_executor = ThreadPoolExecutor(max_workers=1)

_jobs: dict[str, dict] = {}
# room stem -> job_id of the most recently submitted render for that room.
_room_current: dict[str, str] = {}


def _job(job_id: str, **fields) -> dict:
    return _jobs.setdefault(job_id, {"job_id": job_id, **fields})


def _is_current(job_id: str, room_key: str) -> bool:
    return _room_current.get(room_key) == job_id


def _run_render_job(
    job_id: str, room_path: str, room_key: str, tile_path: str, **params
) -> None:
    def report(fraction: float, message: str) -> None:
        job = _jobs.get(job_id)
        if job is not None:
            job["progress"] = fraction
            job["message"] = message

    def finish(status: str, message: str) -> None:
        final = _jobs.setdefault(job_id, {})
        final.update(status=status, message=message)

    job = _jobs.get(job_id)
    if job is not None:
        job["status"] = "processing"

    if not _is_current(job_id, room_key):
        finish("superseded", "Superseded by a newer request")
        return

    try:
        output = services.render.render(
            room_path=room_path,
            tile_path=tile_path,
            progress_cb=report,
            **params,
        )
        if not _is_current(job_id, room_key):
            finish("superseded", "Superseded by a newer request")
            return
        filename = Path(output).name
        final = _jobs.setdefault(job_id, {})
        final.update(
            status="done",
            progress=1.0,
            message="Done",
            image=f"/output/{filename}",
            filename=filename,
        )
    except Exception as exc:  # pragma: no cover - job errors are surfaced by poll
        logger.exception("Render job %s failed", job_id)
        job = _jobs.setdefault(job_id, {})
        job.update(status="error", message=f"Render failed: {exc}")


@router.post("")
async def render(request: RenderRequest):
    try:
        room = services.rooms.get_room(request.room)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        tile = services.tiles.get_tile(request.tile)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    room_key = Path(room).stem
    previous = _room_current.get(room_key)
    if previous:
        old = _jobs.get(previous)
        if old is not None and old.get("status") in ("queued", "processing"):
            old["status"] = "superseded"
            old["message"] = "Superseded by a newer request"

    job_id = uuid.uuid4().hex[:10]
    _room_current[room_key] = job_id
    _job(job_id, status="queued", progress=0.0, message="Queued")

    _executor.submit(
        _run_render_job,
        job_id,
        str(room),
        room_key,
        tile["image_path"],
        tile_size_mm=request.tile_size,
        grout_width=request.grout_width,
        grout_color=tuple(request.grout_color),
        pattern=request.pattern,
    )

    return {"job_id": job_id, "status": "queued", "progress": 0.0, "message": "Queued"}


@router.get("/{job_id}")
def render_status(job_id: str):
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job")
    return job
