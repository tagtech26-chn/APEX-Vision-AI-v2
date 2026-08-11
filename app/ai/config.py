"""AI pipeline configuration and provider selection."""

from __future__ import annotations

from pathlib import Path

from app.core.config import settings

VALID_PROVIDERS = {"auto", "heavy", "light"}

DETECTION_PROMPTS = {
    "floor": "floor, ground, tiles, marble floor, ceramic floor",
    "wall": "wall",
    "ceiling": "ceiling",
    "furniture": "table, chair, sofa, bed, cabinet, door, window",
}


def resolve_provider(requested: str | None = None) -> str:
    """Normalise the requested provider and validate it."""
    provider = (requested or settings.ai_provider).strip().lower()
    if provider not in VALID_PROVIDERS:
        raise ValueError(
            f"Unknown AI provider {provider!r}. "
            f"Expected one of: {', '.join(sorted(VALID_PROVIDERS))}."
        )
    return provider


def _missing_path(label: str, value: str, *, directory: bool = False) -> str | None:
    """Return a readable readiness error for a configured model path."""
    if not value.strip():
        return f"{label} is not configured"
    path = Path(value).expanduser()
    if directory and not path.is_dir():
        return f"{label} not found: {path}"
    if not directory and not path.is_file():
        return f"{label} not found: {path}"
    return None


def heavy_models_available() -> tuple[bool, list[str]]:
    """Check the complete heavy stack before selecting it.

    Import checks alone are not enough: the heavy provider also requires model
    repositories, configuration files and checkpoints. Reporting those failures
    here prevents an "auto" deployment from selecting heavy and then failing on
    the first render request.
    """
    missing: list[str] = []

    for package in ("groundingdino", "sam2", "torch"):
        try:
            __import__(package)
        except Exception:
            missing.append(package)

    checks = (
        ("GROUNDING_DINO_CONFIG", settings.grounding_dino_config, False),
        ("GROUNDING_DINO_CKPT", settings.grounding_dino_ckpt, False),
        ("SAM2_CONFIG_DIR", settings.sam2_config_dir, True),
        ("SAM2_CKPT", settings.sam2_ckpt, False),
        ("DEPTH_ANYTHING_ROOT", settings.depth_anything_root, True),
        ("DEPTH_ANYTHING_CKPT", settings.depth_anything_ckpt, False),
    )
    for label, value, directory in checks:
        error = _missing_path(label, value, directory=directory)
        if error:
            missing.append(error)

    if settings.sam2_config_dir.strip() and settings.sam2_config_file.strip():
        sam2_config = Path(settings.sam2_config_dir).expanduser() / settings.sam2_config_file
        if not sam2_config.is_file():
            missing.append(f"SAM2_CONFIG_FILE not found: {sam2_config}")

    return (not missing), missing
