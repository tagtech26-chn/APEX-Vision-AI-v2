"""SAM2 segmentation provider (heavy provider)."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.ai.segmentation.base import Segmenter
from app.core.config import settings


class SAM2Provider(Segmenter):
    """Segment Anything 2 box-prompted segmenter."""

    name = "sam2"

    def __init__(
        self,
        config_dir: str | None = None,
        config_file: str | None = None,
        checkpoint_path: str | None = None,
    ) -> None:
        self.config_dir = config_dir or settings.sam2_config_dir
        self.config_file = config_file or settings.sam2_config_file
        self.checkpoint_path = checkpoint_path or settings.sam2_ckpt

        config_path = Path(self.config_dir).expanduser() / self.config_file
        checkpoint = Path(self.checkpoint_path).expanduser()
        if not config_path.is_file():
            raise FileNotFoundError(f"SAM2 config not found: {config_path}")
        if not checkpoint.is_file():
            raise FileNotFoundError(f"SAM2 checkpoint not found: {checkpoint}")

        from hydra.core.global_hydra import GlobalHydra
        from hydra import initialize_config_dir

        if GlobalHydra.instance().is_initialized():
            GlobalHydra.instance().clear()

        initialize_config_dir(
            version_base=None,
            config_dir=str(Path(self.config_dir).expanduser().resolve()),
        )

        from sam2.build_sam import build_sam2
        from sam2.sam2_image_predictor import SAM2ImagePredictor

        self.device = self._resolve_device()
        self.model = build_sam2(
            config_file=self.config_file,
            ckpt_path=str(checkpoint),
            device=self.device,
            mode="eval",
        )
        self.predictor = SAM2ImagePredictor(self.model)

    @staticmethod
    def _resolve_device() -> str:
        requested = settings.ai_device
        if requested == "cuda":
            import torch

            if not torch.cuda.is_available():
                raise RuntimeError("APEX_AI_DEVICE=cuda was requested but CUDA is unavailable")
            return "cuda"
        if requested == "cpu":
            return "cpu"
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def segment(
        self,
        image: np.ndarray,
        box: tuple[int, int, int, int] | None = None,
        points: np.ndarray | None = None,
    ) -> np.ndarray:
        masks = self.segment_many(image, boxes=[box] if box is not None else None, points=points)
        return masks[0]

    def segment_many(
        self,
        image: np.ndarray,
        boxes: list[tuple[int, int, int, int]] | None = None,
        points: np.ndarray | None = None,
    ) -> list[np.ndarray]:
        """Segment several prompts after a single image embedding."""
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.predictor.set_image(rgb)

        if boxes is None:
            kwargs: dict = {"multimask_output": False}
            if points is not None:
                kwargs["point_coords"] = points.astype(np.float32)
                kwargs["point_labels"] = np.ones(len(points), dtype=np.int32)
            masks, _, _ = self.predictor.predict(**kwargs)
            return [(masks[0] * 255).astype(np.uint8)]

        results: list[np.ndarray] = []
        for box in boxes:
            masks, _, _ = self.predictor.predict(
                box=np.asarray(box, dtype=np.float32)[None, :],
                multimask_output=False,
            )
            results.append((masks[0] * 255).astype(np.uint8))
        return results
