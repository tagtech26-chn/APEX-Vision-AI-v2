"""Deterministic scale diagnostics for physical tile projection."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectionScale:
    """Physical-to-canvas scale information used for render diagnostics."""

    tile_size_mm: int
    tile_pixels: int
    plane_span_pixels: int
    estimated_tiles_across: float
    pixels_per_mm: float

    def as_dict(self) -> dict[str, float | int]:
        return {
            "tile_size_mm": self.tile_size_mm,
            "tile_pixels": self.tile_pixels,
            "plane_span_pixels": self.plane_span_pixels,
            "estimated_tiles_across": self.estimated_tiles_across,
            "pixels_per_mm": self.pixels_per_mm,
        }


def evaluate_projection_scale(
    tile_size_mm: int,
    tile_pixels: int,
    plane_span_pixels: int = 2048,
    reference_floor_mm: int = 7800,
) -> ProjectionScale:
    """Return deterministic scale diagnostics without changing rendering.

    The reference floor span is the calibrated physical span represented by the
    projector's plane canvas. Keeping the calculation here makes the scale
    contract testable independently from OpenCV rendering.
    """
    if tile_size_mm <= 0:
        raise ValueError("tile_size_mm must be positive")
    if tile_pixels <= 0:
        raise ValueError("tile_pixels must be positive")
    if plane_span_pixels <= 0:
        raise ValueError("plane_span_pixels must be positive")
    if reference_floor_mm <= 0:
        raise ValueError("reference_floor_mm must be positive")

    return ProjectionScale(
        tile_size_mm=int(tile_size_mm),
        tile_pixels=int(tile_pixels),
        plane_span_pixels=int(plane_span_pixels),
        estimated_tiles_across=reference_floor_mm / float(tile_size_mm),
        pixels_per_mm=tile_pixels / float(tile_size_mm),
    )
