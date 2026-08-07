"""DepthAnythingV2 depth estimator (heavy provider)."""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

from app.ai.depth.base import DepthEstimator
from app.core.config import settings


class DepthAnythingProvider(DepthEstimator):
    """DepthAnythingV2 metric-estimation provider."""

    name = "depth_anything_v2"

    def __init__(
        self,
        root: str | None = None,
        checkpoint_path: str | None = None,
    ) -> None:
        self.root = Path(root or settings.depth_anything_root)
        self.checkpoint_path = Path(checkpoint_path or settings.depth_anything_ckpt)

        if not self.root.exists():
            raise FileNotFoundError(f"Depth-Anything-V2 root not found: {self.root}")
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(
                f"DepthAnythingV2 checkpoint not found: {self.checkpoint_path}"
            )

        if str(self.root) not in sys.path:
            sys.path.insert(0, str(self.root))

        import torch
        from depth_anything_v2.dpt import DepthAnythingV2

        self.model = DepthAnythingV2(encoder="vitl")

        state = torch.load(self.checkpoint_path, map_location="cpu")
        self.model.load_state_dict(state)
        self.model.to("cpu")
        self.model.eval()

        self._torch_no_grad = torch.no_grad()

    def predict(self, image: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        with self._torch_no_grad:
            depth = self.model.infer_image(rgb)
        return self.normalise(depth)
