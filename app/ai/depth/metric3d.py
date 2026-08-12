"""Metric3D depth provider for the isolated v2.2 geometry path.

The provider exposes metric depth plus optional XYZ/normals to the v2.2 scene
analyzer. When a real Metric3D runtime is not configured, it uses a deterministic
CPU fallback explicitly marked as development-only; it never silently pretends
that fallback depth is model inference.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

from app.ai.depth.base import DepthEstimator

logger = logging.getLogger("apex.ai")


@dataclass(slots=True)
class MetricIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float


class Metric3DProvider(DepthEstimator):
    name = "metric3d_v2"

    def __init__(self, device: str = "auto", model_path: str | None = None, checkpoint: str | None = None) -> None:
        self.device = device
        self.model_path = model_path or ""
        self.checkpoint = checkpoint or ""
        self.last_metric_depth: np.ndarray | None = None
        self.last_points: np.ndarray | None = None
        self.last_intrinsics: MetricIntrinsics | None = None
        self.last_normals: np.ndarray | None = None
        self.used_fallback = False
        self._model = None

        if self.device == "auto":
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                self.device = "cpu"

        self._try_load_model()
        if self._model is None:
            logger.warning(
                "Metric3D %s development mode: real Metric3D disabled; using deterministic geometry-safe depth fallback.",
                self.device.upper(),
            )

    def _try_load_model(self) -> None:
        """Load only an explicitly supplied TorchScript model.

        We deliberately avoid implicit network downloads in the production
        application. A deployment can provide a local TorchScript checkpoint;
        unsupported model formats remain on the deterministic fallback path.
        """
        if not self.checkpoint:
            return
        try:
            import torch

            self._model = torch.jit.load(self.checkpoint, map_location=self.device)
            self._model.eval()
            logger.info("Metric3D local TorchScript model loaded: %s", self.checkpoint)
        except Exception as exc:
            self._model = None
            logger.warning("Metric3D model load failed (%s); using CPU-safe fallback.", exc)

    @staticmethod
    def _intrinsics(height: int, width: int) -> MetricIntrinsics:
        focal = 0.92 * max(height, width)
        return MetricIntrinsics(
            fx=float(focal),
            fy=float(focal),
            cx=float(width - 1) * 0.5,
            cy=float(height - 1) * 0.5,
        )

    @staticmethod
    def _fallback_depth(image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
        # Perspective-safe monotonic ground distance. The lower image is
        # closer to the camera; depth is expressed in metres.
        z_near = 0.65
        z_far = 5.50
        depth = z_near + (yy ** 1.65) * (z_far - z_near)
        depth = np.repeat(depth, w, axis=1)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        local = gray - cv2.GaussianBlur(gray, (0, 0), 7.0)
        # Keep texture influence deliberately tiny so tile/furniture edges do
        # not become synthetic metric planes.
        depth *= 1.0 + np.clip(local, -0.06, 0.06) * 0.08
        return depth.astype(np.float32)

    @staticmethod
    def _points_from_depth(depth: np.ndarray, intrinsics: MetricIntrinsics) -> np.ndarray:
        h, w = depth.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        z = np.maximum(depth.astype(np.float32), 1e-4)
        x = (xx.astype(np.float32) - intrinsics.cx) * z / intrinsics.fx
        y = (yy.astype(np.float32) - intrinsics.cy) * z / intrinsics.fy
        return np.stack((x, y, z), axis=-1).astype(np.float32)

    @staticmethod
    def _normals(points: np.ndarray) -> np.ndarray:
        dzdx = cv2.Sobel(points[:, :, 2], cv2.CV_32F, 1, 0, ksize=3)
        dzdy = cv2.Sobel(points[:, :, 2], cv2.CV_32F, 0, 1, ksize=3)
        nx = -dzdx
        ny = -dzdy
        nz = np.ones_like(dzdx)
        normals = np.stack((nx, ny, nz), axis=-1)
        length = np.linalg.norm(normals, axis=2, keepdims=True)
        return normals / np.maximum(length, 1e-6)

    def _predict_model(self, image: np.ndarray) -> np.ndarray | None:
        if self._model is None:
            return None
        try:
            import torch

            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            tensor = torch.from_numpy(rgb).permute(2, 0, 1).float().div(255.0).unsqueeze(0).to(self.device)
            with torch.inference_mode():
                output = self._model(tensor)
            if isinstance(output, (tuple, list)):
                output = output[0]
            if hasattr(output, "detach"):
                output = output.detach().float().cpu().numpy()
            depth = np.asarray(output, dtype=np.float32).squeeze()
            if depth.shape != image.shape[:2] or not np.isfinite(depth).any():
                raise ValueError("Metric3D TorchScript output shape is invalid")
            finite = np.isfinite(depth)
            lo, hi = np.percentile(depth[finite], [2, 98])
            depth = np.clip(depth, lo, hi)
            # TorchScript exports vary in whether they emit inverse depth or
            # metric depth. Require positive metric scale from the deployment;
            # otherwise fall back rather than inventing metres.
            if float(np.median(depth[finite])) <= 0:
                raise ValueError("Metric3D output is not positive")
            return depth.astype(np.float32)
        except Exception as exc:
            logger.warning("Metric3D inference failed (%s); using fallback.", exc)
            return None

    def predict(self, image: np.ndarray) -> np.ndarray:
        if image is None or image.ndim != 3:
            raise ValueError("Metric3DProvider expects a BGR image.")

        depth = self._predict_model(image)
        self.used_fallback = depth is None
        if depth is None:
            depth = self._fallback_depth(image)

        h, w = image.shape[:2]
        intrinsics = self._intrinsics(h, w)
        points = self._points_from_depth(depth, intrinsics)
        normals = self._normals(points)

        self.last_metric_depth = depth.astype(np.float32)
        self.last_intrinsics = intrinsics
        self.last_points = points
        self.last_normals = normals.astype(np.float32)
        return self.last_metric_depth
