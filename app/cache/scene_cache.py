"""Scene result caching."""

from __future__ import annotations

import pickle
from pathlib import Path

from app.ai.scene.result import SceneResult
from app.core.config import settings


class SceneCache:
    """Persists analysed SceneResult objects so re-renders are instant."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else settings.scenes_dir
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, room_name: str) -> Path:
        safe = room_name.replace("\\", "_").replace("/", "_").strip()
        if not safe:
            raise ValueError("Room name cannot be empty.")
        return self.root / f"{safe}.scene"

    def exists(self, room_name: str) -> bool:
        return self._path(room_name).exists()

    def save(self, room_name: str, scene: SceneResult) -> None:
        with self._path(room_name).open("wb") as fp:
            pickle.dump(scene, fp)

    def load(self, room_name: str) -> SceneResult:
        path = self._path(room_name)
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open("rb") as fp:
            scene = pickle.load(fp)
        if not isinstance(scene, SceneResult):
            raise TypeError(f"Corrupt scene cache: {path}")
        return scene

    def delete(self, room_name: str) -> None:
        path = self._path(room_name)
        if path.exists():
            path.unlink()

    def clear(self) -> None:
        for file in self.root.glob("*.scene"):
            file.unlink()
