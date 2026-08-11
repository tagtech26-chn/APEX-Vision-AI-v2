"""GroundingDINO object detector (heavy provider)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import numpy as np

from app.ai.detection.base import Detection, ObjectDetector
from app.core.config import settings


class GroundingDINOProvider(ObjectDetector):
    """GroundingDINO text-prompted detector."""

    name = "groundingdino"

    def __init__(
        self,
        config_path: str | None = None,
        checkpoint_path: str | None = None,
    ) -> None:
        self.config_path = config_path or settings.grounding_dino_config
        self.checkpoint_path = checkpoint_path or settings.grounding_dino_ckpt

        for label, path in (
            ("config", self.config_path),
            ("checkpoint", self.checkpoint_path),
        ):
            if not path or not Path(path).expanduser().is_file():
                raise FileNotFoundError(f"GroundingDINO {label} not found: {path or '<unset>'}")

        self.device = self._resolve_device()
        from groundingdino.util.inference import load_model

        self.model = load_model(
            self.config_path,
            self.checkpoint_path,
            device=self.device,
        )

    @staticmethod
    def _resolve_device() -> str:
        requested = settings.ai_device
        if requested in {"cpu", "cuda"}:
            if requested == "cuda":
                import torch

                if not torch.cuda.is_available():
                    raise RuntimeError("APEX_AI_DEVICE=cuda was requested but CUDA is unavailable")
            return requested

        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def detect(
        self,
        image: np.ndarray,
        prompt: str,
        box_threshold: float = 0.35,
        text_threshold: float = 0.25,
    ) -> list[Detection]:
        from groundingdino.util.inference import predict

        temp_path = self._to_temp(image)
        try:
            image_source, image_tensor = self._load_image(temp_path)
            h, w = image_source.shape[:2]

            boxes, logits, phrases = predict(
                model=self.model,
                image=image_tensor,
                caption=prompt,
                box_threshold=box_threshold,
                text_threshold=text_threshold,
                device=self.device,
            )

            detections: list[Detection] = []
            for box, score, phrase in zip(boxes, logits, phrases):
                cx, cy, bw, bh = box.detach().cpu().numpy() * np.array([w, h, w, h])
                x1 = max(0, min(w - 1, int(cx - bw / 2)))
                y1 = max(0, min(h - 1, int(cy - bh / 2)))
                x2 = max(x1 + 1, min(w, int(cx + bw / 2)))
                y2 = max(y1 + 1, min(h, int(cy + bh / 2)))
                detections.append(
                    Detection(
                        label=str(phrase).strip(),
                        score=float(score.detach().cpu().item()),
                        box=(x1, y1, x2, y2),
                    )
                )

            return detections
        finally:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass

    @staticmethod
    def _to_temp(image: np.ndarray) -> str:
        """Write a unique temporary image so concurrent renders cannot collide."""
        handle = tempfile.NamedTemporaryFile(
            prefix="apex-dino-",
            suffix=".png",
            delete=False,
        )
        handle.close()
        path = Path(handle.name)
        if not cv2.imwrite(str(path), image):
            path.unlink(missing_ok=True)
            raise IOError(f"Unable to write temporary detector image: {path}")
        return str(path)

    @staticmethod
    def _load_image(image_path: str):
        from groundingdino.util.inference import load_image

        return load_image(image_path)
