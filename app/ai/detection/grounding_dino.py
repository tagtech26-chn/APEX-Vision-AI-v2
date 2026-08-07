"""GroundingDINO object detector (heavy provider)."""

from __future__ import annotations

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
            if not Path(path).exists():
                raise FileNotFoundError(f"GroundingDINO {label} not found: {path}")

        from groundingdino.util.inference import load_model

        self.model = load_model(self.config_path, self.checkpoint_path)

    def detect(
        self,
        image: np.ndarray,
        prompt: str,
        box_threshold: float = 0.35,
        text_threshold: float = 0.25,
    ) -> list[Detection]:
        from groundingdino.util.inference import predict

        temp = self._to_temp(image)

        image_source, image_tensor = self._load_image(temp)
        h, w = image_source.shape[:2]

        boxes, logits, phrases = predict(
            model=self.model,
            image=image_tensor,
            caption=prompt,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
            device="cpu",
        )

        detections: list[Detection] = []
        for box, score, phrase in zip(boxes, logits, phrases):
            cx, cy, bw, bh = box.cpu().numpy() * np.array([w, h, w, h])
            x1 = int(cx - bw / 2)
            y1 = int(cy - bh / 2)
            x2 = int(cx + bw / 2)
            y2 = int(cy + bh / 2)
            detections.append(
                Detection(
                    label=phrase,
                    score=float(score),
                    box=(x1, y1, x2, y2),
                )
            )

        return detections

    # -----------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------

    @staticmethod
    def _to_temp(image: np.ndarray) -> str:
        import tempfile

        temp = Path(tempfile.gettempdir()) / "apex_detection_input.png"
        cv2.imwrite(str(temp), image)
        return str(temp)

    @staticmethod
    def _load_image(image_path: str):
        from groundingdino.util.inference import load_image

        return load_image(image_path)
