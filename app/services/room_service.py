"""Room service: resolve room ids to image paths."""

from __future__ import annotations

import logging
from pathlib import Path

import cv2

from app.core.config import settings

logger = logging.getLogger("apex.rooms")

SUPPORTED_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")
THUMB_WIDTH = 360


class RoomService:
    """Maps room ids (1-based) to image files in the rooms directory."""

    def __init__(self, room_root: str | Path | None = None) -> None:
        self.room_root = Path(room_root) if room_root else settings.rooms_dir

    def list_rooms(self) -> list[dict]:
        files = self._files()
        thumbs_dir = self.room_root / "thumbs"
        rooms = []
        for index, file in enumerate(files, start=1):
            display_name = (
                file.stem.replace("_", " ").replace("-", " ").title()
            )
            thumb = self._ensure_thumbnail(file, thumbs_dir)
            relative = thumb.relative_to(self.room_root).as_posix()
            rooms.append(
                {
                    "id": index,
                    "name": display_name,
                    "image": f"/assets/rooms/{file.name}",
                    "thumbnail": f"/assets/rooms/{relative}",
                }
            )
        return rooms

    def _ensure_thumbnail(self, source: Path, thumbs_dir: Path) -> Path:
        """Return a downscaled JPEG for ``source``, generating it if stale/missing."""
        thumb = thumbs_dir / f"{source.stem}.jpg"
        try:
            if thumb.exists() and thumb.stat().st_mtime >= source.stat().st_mtime:
                return thumb
            img = cv2.imread(str(source), cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError(f"cannot read image: {source}")
            height, width = img.shape[:2]
            new_width = min(THUMB_WIDTH, width)
            new_height = max(1, round(height * new_width / width))
            resized = cv2.resize(
                img, (new_width, new_height), interpolation=cv2.INTER_AREA
            )
            thumbs_dir.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(
                str(thumb), resized, [cv2.IMWRITE_JPEG_QUALITY, 82]
            ):
                raise OSError(f"failed to write {thumb}")
            return thumb
        except Exception:
            logger.exception("thumbnail generation failed for %s", source)
            return source

    def get_room(self, room_id: int) -> Path:
        files = self._files()
        if room_id < 1 or room_id > len(files):
            raise ValueError(f"Invalid room id: {room_id}")
        return files[room_id - 1]

    def _files(self) -> list[Path]:
        if not self.room_root.exists():
            return []
        return sorted(
            f
            for f in self.room_root.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_SUFFIXES
        )
