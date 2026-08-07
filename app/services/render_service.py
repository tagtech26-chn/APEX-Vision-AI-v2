"""Render service: orchestrates scene analysis + tile rendering."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import cv2

from app.ai.scene.result import SceneResult
from app.cache.scene_cache import SceneCache
from app.core.config import settings
from app.renderer.tile_renderer import TileRenderer

logger = logging.getLogger("apex.render")

# Guards one-time AI model loading (startup warm-up vs. first render request).
_ANALYZER_LOCK = threading.Lock()


class RenderService:
    """Loads or builds a SceneResult for a room, then renders a tile into it."""

    def __init__(
        self,
        analyzer=None,
        cache: SceneCache | None = None,
        renderer: TileRenderer | None = None,
    ) -> None:
        self.cache = cache or SceneCache()
        self.renderer = renderer or TileRenderer(
            debug=settings.write_debug_images
        )
        self.analyzer = analyzer

    def get_analyzer(self):
        if self.analyzer is None:
            with _ANALYZER_LOCK:
                if self.analyzer is None:
                    from app.ai.scene.analyzer import build_scene_analyzer

                    self.analyzer = build_scene_analyzer(settings.ai_provider)
        return self.analyzer

    def render(
        self,
        room_path: str | Path,
        tile_path: str | Path,
        tile_size_mm: int = 600,
        grout_width: int = 2,
        grout_color=(220, 220, 220),
        pattern: str = "Straight",
        alpha: float = 0.92,
        progress_cb=None,
    ) -> str:
        room_path = Path(room_path)
        if not room_path.exists():
            raise FileNotFoundError(f"Room image not found: {room_path}")

        def report(fraction: float, message: str) -> None:
            if progress_cb is not None:
                progress_cb(fraction, message)

        room_key = room_path.stem

        scene = self._load_or_build_scene(room_path, progress_cb=progress_cb)

        tile = cv2.imread(str(tile_path))
        if tile is None:
            raise ValueError(f"Unable to load tile: {tile_path}")

        report(0.92, "Rendering tiles...")
        logger.info(
            "Rendering room=%s tile=%s size=%smm grout=%s pattern=%s",
            room_key,
            Path(tile_path).name,
            tile_size_mm,
            grout_width,
            pattern,
        )

        result = self.renderer.render(
            scene=scene,
            tile=tile,
            tile_size_mm=tile_size_mm,
            grout_width=grout_width,
            grout_color=grout_color,
            pattern=pattern,
            alpha=alpha,
        )

        report(0.97, "Writing image...")
        output_dir = settings.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{room_key}_render.png"
        cv2.imwrite(str(output_file), result)
        report(1.0, "Done")

        return str(output_file)

    def _cache_key(self, room_path: Path) -> str:
        """Cache key includes the AI provider so switching stacks re-analyses."""
        provider = self.get_analyzer().providers["detector"]
        return f"{room_path.stem}__{provider}__v6"

    @staticmethod
    def _source_fingerprint(room_path: Path) -> str:
        """File fingerprint so a replaced/updated image is re-analysed.

        The cache key is filename-based; without a fingerprint, overwriting a
        room file (e.g. ROOM2.jpg with a new photo) silently reuses the old
        scene and renders the old room.
        """
        stat = room_path.stat()
        return f"{stat.st_size}:{stat.st_mtime_ns}"

    def _load_or_build_scene(
        self, room_path: Path, progress_cb=None
    ) -> SceneResult:
        room_key = self._cache_key(room_path)
        fingerprint = self._source_fingerprint(room_path)

        if self.cache.exists(room_key):
            scene = self.cache.load(room_key)
            cached_fp = scene.metadata.get("source_fingerprint")
            if cached_fp is None:
                # Backfill fingerprints for scenes cached before this change.
                scene.metadata["source_fingerprint"] = fingerprint
                self.cache.save(room_key, scene)
                logger.info("[CACHE] Loading scene (backfilled fp): %s", room_key)
                if progress_cb is not None:
                    progress_cb(0.1, "Loading cached scene...")
                return scene
            if cached_fp == fingerprint:
                logger.info("[CACHE] Loading scene: %s", room_key)
                if progress_cb is not None:
                    progress_cb(0.1, "Loading cached scene...")
                return scene
            logger.info(
                "[CACHE] Source changed for %s, re-analysing.", room_path.name
            )

        logger.info("[AI] Analysing room: %s", room_path.name)
        analyzer = self.get_analyzer()
        scene = analyzer.analyze(room_path, progress_cb=progress_cb)
        scene.metadata["source_fingerprint"] = fingerprint
        self.cache.save(room_key, scene)
        return scene
