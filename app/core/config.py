"""Application settings, driven by environment variables with sane defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    """Runtime configuration for the whole application."""

    # -----------------------------------------------------------
    # Server
    # -----------------------------------------------------------
    host: str = field(default_factory=lambda: _env("APEX_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _env_int("APEX_PORT", 8000))
    debug: bool = field(default_factory=lambda: _env_bool("APEX_DEBUG", False))
    write_debug_images: bool = field(
        default_factory=lambda: _env_bool("APEX_WRITE_DEBUG", False)
    )

    # -----------------------------------------------------------
    # Paths (relative to project root unless absolute)
    # -----------------------------------------------------------
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent
    )

    assets_dir: Path = field(default_factory=Path)
    output_dir: Path = field(default_factory=Path)
    uploads_dir: Path = field(default_factory=Path)
    catalog_dir: Path = field(default_factory=Path)
    scenes_dir: Path = field(default_factory=Path)

    # -----------------------------------------------------------
    # AI provider selection
    #   auto  -> use the heavy pipeline when the models are
    #            reachable, otherwise fall back to heuristics
    #   heavy -> always try GroundingDINO + SAM2 + DepthAnythingV2
    #   light -> always use the OpenCV heuristic pipeline
    # -----------------------------------------------------------
    ai_provider: str = field(
        default_factory=lambda: _env("APEX_AI_PROVIDER", "auto").lower()
    )

    # -----------------------------------------------------------
    # Heavy model paths (all optional; can be overridden via env)
    # -----------------------------------------------------------
    grounding_dino_config: str = field(
        default_factory=lambda: _env(
            "GROUNDING_DINO_CONFIG",
            r"D:\Projects\GroundingDINO\groundingdino\config\GroundingDINO_SwinT_OGC.py",
        )
    )
    grounding_dino_ckpt: str = field(
        default_factory=lambda: _env(
            "GROUNDING_DINO_CKPT",
            r"D:\Projects\GroundingDINO\weights\groundingdino_swint_ogc.pth",
        )
    )
    sam2_config_dir: str = field(
        default_factory=lambda: _env(
            "SAM2_CONFIG_DIR",
            r"D:\Projects\sam2\sam2\configs",
        )
    )
    sam2_config_file: str = field(
        default_factory=lambda: _env("SAM2_CONFIG_FILE", "sam2.1/sam2.1_hiera_l.yaml")
    )
    sam2_ckpt: str = field(
        default_factory=lambda: _env(
            "SAM2_CKPT",
            r"D:\Projects\APEX-Vision-AI-v2\models\sam2\checkpoints\sam2.1_hiera_large.pt",
        )
    )
    depth_anything_root: str = field(
        default_factory=lambda: _env(
            "DEPTH_ANYTHING_ROOT",
            r"D:\Projects\Depth-Anything-V2\Depth-Anything-V2",
        )
    )
    depth_anything_ckpt: str = field(
        default_factory=lambda: _env(
            "DEPTH_ANYTHING_CKPT",
            r"D:\Projects\Depth-Anything-V2\Depth-Anything-V2\checkpoints\depth_anything_v2_vitl.pth",
        )
    )

    # -----------------------------------------------------------
    # Render defaults
    # -----------------------------------------------------------
    render_tile_size_mm: int = field(default_factory=lambda: _env_int("APEX_TILE_MM", 600))
    render_grout_width: int = field(default_factory=lambda: _env_int("APEX_GROUT", 2))
    render_grout_color: tuple[int, int, int] = field(default_factory=lambda: (220, 220, 220))
    render_alpha: float = field(default_factory=lambda: float(_env("APEX_ALPHA", "0.92")))
    render_pattern: str = field(default_factory=lambda: _env("APEX_PATTERN", "Straight"))
    # Largest dimension of a room image processed by AI + renderer. Room photos
    # are often 4K+; downscaling cuts analysis and render time ~10x with no
    # visible loss in the browser (output is shown at ~1-2K wide).
    render_max_dim: int = field(default_factory=lambda: _env_int("APEX_RENDER_MAX_DIM", 2048))

    def __post_init__(self) -> None:
        root = self.project_root

        self.assets_dir = Path(_env("APEX_ASSETS", str(root / "assets")) or root / "assets")
        self.output_dir = Path(_env("APEX_OUTPUT", str(root / "output")) or root / "output")
        self.uploads_dir = Path(_env("APEX_UPLOADS", str(root / "uploads")) or root / "uploads")
        self.catalog_dir = Path(_env("APEX_CATALOG", str(root / "catalog")) or root / "catalog")
        self.scenes_dir = Path(_env("APEX_SCENES", str(self.assets_dir / "scenes")) or self.assets_dir / "scenes")

        for folder in (self.assets_dir, self.output_dir, self.uploads_dir, self.catalog_dir, self.scenes_dir):
            folder.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------
    # Convenience accessors
    # -----------------------------------------------------------
    @property
    def rooms_dir(self) -> Path:
        path = self.assets_dir / "rooms"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def tile_images_dir(self) -> Path:
        path = self.assets_dir / "tiles" / "images"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def tile_thumbs_dir(self) -> Path:
        path = self.assets_dir / "tiles" / "thumbnails"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def catalog_file(self) -> Path:
        return self.catalog_dir / "tiles.json"


settings = Settings()
