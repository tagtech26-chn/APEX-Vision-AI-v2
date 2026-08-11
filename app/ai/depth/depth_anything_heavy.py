"""Device-aware DepthAnythingV2 depth estimator for the heavy provider."""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

from app.ai.depth.base import DepthEstimator
from app.core.config import settings


class DepthAnythingHeavyProvider(DepthEstimator):
    """DepthAnythingV2 provider using the configured CPU/CUDA device."""

    name = "depth_anything_v2"

    def __init__(self, root: str | None = None, checkpoint_path: str | None = None) -> None:
        self.root = Path(root or settings.depth_anything_root).expanduser()
        self.checkpoint_path = Path(checkpoint_path or settings.depth_anything_ckpt).expanduser()

        if not self.root.is_dir():
            raise FileNotFoundError(f"Depth-Anything-V2 root not found: {self.root}")
        if not self.checkpoint_path.is_file():
            raise FileNotFoundError(f"DepthAnythingV2 checkpoint not found: {self.checkpoint_path}")

        if str(self.root) not in sys.path:
            sys.path.insert(0, str(self.root))

        import torch
        from depth_anything_v2.dpt import DepthAnythingV2

        self.device = self._resolve_device(torch)
        self.model = DepthAnythingV2(encoder="vitl")
        state = torch.load(self.checkpoint_path, map_location="cpu")
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        elif isinstance(state, dict) and isinstance(state.get("model"), dict):
            state = state["model"]
        self.model.load_state_dict(state)
        self.model.to(self.device)
        self.model.eval()
        self._torch = torch

    @staticmethod
    def _resolve_device(torch) -> str:
        requested = settings.ai_device
        if requested == "cuda":
            if not torch.cuda.is_available():
                raise RuntimeError("APEX_AI_DEVICE=cuda was requested but CUDA is unavailable")
            return "cuda"
        if requested == "cpu":
            return "cpu"
        return "cuda" if torch.cuda.is_available() else "cpu"

    def predict(self, image: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        with self._torch.no_grad():
            depth = self.model.infer_image(rgb)
        return self.normalise(depth)
