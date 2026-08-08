"""Secure scene-result caching for APEX Vision AI."""

from __future__ import annotations

import hashlib
import hmac
import os
import pickle
import tempfile
from pathlib import Path

from app.ai.scene.result import SceneResult
from app.core.config import settings


class SceneCache:
    """Persist analysed scenes with HMAC integrity protection when configured."""

    def __init__(self, root: str | Path | None = None, signing_key: str | None = None) -> None:
        self.root = Path(root) if root else settings.scenes_dir
        self.root.mkdir(parents=True, exist_ok=True)
        self._signing_key = (signing_key if signing_key is not None else os.getenv("APEX_CACHE_SIGNING_KEY", "")).encode()

    @property
    def enabled(self) -> bool:
        return bool(self._signing_key)

    def _path(self, room_name: str) -> Path:
        name = room_name.strip()
        if not name or name in {".", ".."} or "/" in name or "\\" in name:
            raise ValueError("Room name must be a single safe path component.")
        return self.root / f"{name}.scene"

    def _signature(self, payload: bytes) -> bytes:
        return hmac.new(self._signing_key, payload, hashlib.sha256).digest()

    def exists(self, room_name: str) -> bool:
        return self.enabled and self._path(room_name).exists()

    def save(self, room_name: str, scene: SceneResult) -> None:
        if not self.enabled:
            return
        path = self._path(room_name)
        payload = pickle.dumps(scene, protocol=pickle.HIGHEST_PROTOCOL)
        envelope = self._signature(payload) + payload
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as fp:
                fp.write(envelope)
                fp.flush()
                os.fsync(fp.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def load(self, room_name: str) -> SceneResult:
        if not self.enabled:
            raise FileNotFoundError("Persistent scene cache is disabled")
        path = self._path(room_name)
        if not path.exists():
            raise FileNotFoundError(path)
        envelope = path.read_bytes()
        digest_size = hashlib.sha256().digest_size
        if len(envelope) <= digest_size:
            raise ValueError(f"Invalid scene cache: {path}")
        signature, payload = envelope[:digest_size], envelope[digest_size:]
        if not hmac.compare_digest(signature, self._signature(payload)):
            raise ValueError(f"Scene cache integrity check failed: {path}")
        scene = pickle.loads(payload)
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
