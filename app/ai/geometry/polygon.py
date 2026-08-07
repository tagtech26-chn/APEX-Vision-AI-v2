"""Floor polygon extraction from a binary mask."""

from __future__ import annotations

import cv2
import numpy as np


class PolygonEngine:
    """Finds a 4-corner floor polygon from a binary floor mask."""

    @staticmethod
    def largest_contour(mask: np.ndarray) -> np.ndarray:
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            raise RuntimeError("No floor contour found.")
        return max(contours, key=cv2.contourArea)

    def extract(self, mask: np.ndarray) -> np.ndarray:
        """Return a (4, 2) float32 polygon in TL, TR, BR, BL order."""
        contour = self.largest_contour(mask)

        epsilon = 0.02 * cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, epsilon, True)

        if len(polygon) == 4:
            return self.order_points(polygon.reshape(4, 2).astype(np.float32))

        # Preserve perspective: fit a 4-corner quad from the contour hull.
        quad = self.quad_from_points(contour.reshape(-1, 2))
        return self.order_points(quad)

    @staticmethod
    def quad_from_points(points: np.ndarray) -> np.ndarray:
        """Fit a perspective (4, 2) quad to arbitrary floor points.

        Uses the convex hull of the points (which gives the outer floor
        boundary and orders them consistently) and simplifies it to exactly
        four corners so the homography preserves perspective.
        """
        pts = np.asarray(points, dtype=np.float32)
        if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) < 3:
            raise ValueError("At least three (x, y) points are required.")

        hull = cv2.convexHull(pts).reshape(-1, 2).astype(np.float32)
        if len(hull) <= 4:
            quad = np.zeros((4, 2), dtype=np.float32)
            quad[: len(hull)] = hull
            if len(hull) == 3:
                # Closed triangle: duplicate the first vertex to form a quad.
                quad[3] = hull[0]
            return quad

        while len(hull) > 4:
            worst: tuple[float, int] | None = None
            count = len(hull)
            for i in range(count):
                a = hull[i - 1]
                b = hull[i]
                c = hull[(i + 1) % count]
                denom = max(float(np.linalg.norm(c - a)), 1e-6)
                dist = float(np.abs(np.cross(c - a, a - b)) / denom)
                if worst is None or dist < worst[0]:
                    worst = (dist, i)
            hull = np.delete(hull, worst[1], axis=0)

        return hull.astype(np.float32)

    @staticmethod
    def order_points(pts: np.ndarray) -> np.ndarray:
        """Order four points as TL, TR, BR, BL using angle sorting.

        Robust for perspective quads (unlike the classic min/max sum method,
        which assumes near axis-aligned rectangles).
        """
        pts = np.asarray(pts, dtype=np.float32)
        if pts.shape != (4, 2):
            raise ValueError("Exactly four points are required.")

        center = pts.mean(axis=0)
        angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
        return pts[np.argsort(angles)]

    @staticmethod
    def draw(
        image: np.ndarray,
        polygon: np.ndarray,
        labels: bool = True,
    ) -> np.ndarray:
        img = image.copy()
        pts = polygon.astype(np.int32)

        cv2.polylines(img, [pts], True, (0, 255, 0), 4)
        names = ["TL", "TR", "BR", "BL"]
        for i, p in enumerate(pts):
            cx, cy = int(p[0]), int(p[1])
            cv2.circle(img, (cx, cy), 8, (0, 0, 255), -1)
            if labels:
                cv2.putText(
                    img,
                    names[i],
                    (cx + 10, cy - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 0),
                    2,
                )
        return img
