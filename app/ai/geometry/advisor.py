"""Optional Gemini vision advisor for conservative scene geometry."""

from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
from urllib import error, request

import cv2
import numpy as np

logger = logging.getLogger("apex.ai")


class GeometryAdvisor:
    """Interface for an optional geometry advisory pass."""

    name = "none"

    def advise(self, image: np.ndarray, floor_mask: np.ndarray, polygon: np.ndarray) -> dict[str, object]:
        return {"enabled": False, "provider": self.name}


def build_geometry_advisor(provider: str | None = None) -> GeometryAdvisor:
    """Build the configured advisor without making Gemini mandatory."""
    selected = (provider or os.getenv("APEX_GEOMETRY_ADVISOR", "none")).strip().lower()
    if selected in {"", "none", "off", "disabled"}:
        return GeometryAdvisor()
    if selected == "gemini":
        return GeminiGeometryAdvisor()
    raise ValueError("Unknown geometry advisor. Expected: none, gemini")


class GeminiGeometryAdvisor(GeometryAdvisor):
    """Use Gemini vision to identify likely foreground regions and floor geometry.

    Gemini is advisory only: it may remove pixels from the existing semantic
    floor mask, but it is never allowed to manufacture a new floor region.
    """

    name = "gemini"
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: float = 30.0) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.model = model or os.getenv("GEMINI_GEOMETRY_MODEL", "gemini-2.5-flash").strip()
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _image_part(image: np.ndarray) -> dict[str, object]:
        ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        if not ok:
            raise ValueError("Unable to encode scene image for Gemini")
        return {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(encoded.tobytes()).decode("ascii"),
            }
        }

    @staticmethod
    def _prompt(floor_mask: np.ndarray, polygon: np.ndarray) -> str:
        h, w = floor_mask.shape[:2]
        floor_pixels = int((floor_mask > 0).sum())
        quad = np.asarray(polygon, dtype=np.float32).reshape(-1, 2).tolist() if polygon is not None else []
        return f"""You are the geometry advisor for a tile visualization engine.
Analyze the supplied room image conservatively. The existing computer-vision floor mask is authoritative and may only be narrowed, never expanded.

Image size: {w}x{h}
Existing floor pixels: {floor_pixels}
Existing floor polygon: {quad}

Return JSON only with this exact shape:
{{
  "confidence": 0.0,
  "floor_quad": [[x,y],[x,y],[x,y],[x,y]],
  "protected_boxes": [[x0,y0,x1,y1]],
  "notes": "short explanation"
}}

Rules:
- Coordinates are pixel coordinates in the supplied image.
- floor_quad must describe only the visible floor if confidently identifiable; otherwise return [] .
- protected_boxes should contain obvious furniture, rugs, tables, sofas, beds, cabinets, lamps or other non-floor foreground regions that overlap the existing floor mask.
- Do not include walls, ceiling, windows or TV as protected boxes unless they overlap the floor region.
- Do not invent objects.
- Confidence below 0.75 means the caller should treat the advice as informational only.
"""

    def _request(self, image: np.ndarray, prompt: str) -> dict[str, object]:
        payload = {
            "contents": [{"parts": [{"text": prompt}, self._image_part(image)]}],
            "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
        }
        url = self.endpoint.format(model=self.model)
        req = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout) as response:
            raw = json.loads(response.read().decode("utf-8"))
        text = ""
        for candidate in raw.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if part.get("text"):
                    text += part["text"]
        if not text:
            raise ValueError("Gemini returned no geometry advice")
        return json.loads(text)

    def advise(self, image: np.ndarray, floor_mask: np.ndarray, polygon: np.ndarray) -> dict[str, object]:
        if not self.enabled:
            return {"enabled": False, "provider": self.name, "status": "missing_api_key"}
        try:
            data = self._request(image, self._prompt(floor_mask, polygon))
            confidence = float(np.clip(float(data.get("confidence", 0.0)), 0.0, 1.0))
            boxes: list[list[int]] = []
            h, w = floor_mask.shape[:2]
            for raw in data.get("protected_boxes", []) or []:
                if not isinstance(raw, (list, tuple)) or len(raw) != 4:
                    continue
                x0, y0, x1, y1 = [int(float(v)) for v in raw]
                x0, x1 = sorted((max(0, min(w, x0)), max(0, min(w, x1))))
                y0, y1 = sorted((max(0, min(h, y0)), max(0, min(h, y1))))
                if x1 > x0 and y1 > y0:
                    boxes.append([x0, y0, x1, y1])
            return {
                "enabled": True,
                "provider": self.name,
                "status": "ok",
                "model": self.model,
                "confidence": confidence,
                "floor_quad": data.get("floor_quad", []),
                "protected_boxes": boxes,
                "notes": str(data.get("notes", ""))[:1000],
            }
        except (OSError, ValueError, TypeError, json.JSONDecodeError, error.URLError) as exc:
            logger.warning("Gemini geometry advisor unavailable: %s", exc)
            return {"enabled": True, "provider": self.name, "status": "error", "model": self.model, "error": str(exc)[:300]}


def apply_advisor_protection(
    floor_mask: np.ndarray,
    advice: dict[str, object],
    minimum_confidence: float = 0.75,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Apply only high-confidence Gemini boxes inside the existing floor mask."""
    protected = np.zeros_like(floor_mask)
    if not advice.get("enabled") or float(advice.get("confidence", 0.0)) < minimum_confidence:
        return floor_mask, protected, 0

    h, w = floor_mask.shape[:2]
    for raw in advice.get("protected_boxes", []) or []:
        if not isinstance(raw, (list, tuple)) or len(raw) != 4:
            continue
        x0, y0, x1, y1 = [int(v) for v in raw]
        x0, x1 = sorted((max(0, min(w, x0)), max(0, min(w, x1))))
        y0, y1 = sorted((max(0, min(h, y0)), max(0, min(h, y1))))
        if x1 > x0 and y1 > y0:
            protected[y0:y1, x0:x1] = 255

    protected = cv2.bitwise_and(protected, floor_mask)
    protected = cv2.dilate(protected, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    refined = cv2.bitwise_and(floor_mask, cv2.bitwise_not(protected))
    return refined, protected, int((protected > 0).sum())
