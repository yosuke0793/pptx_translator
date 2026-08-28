from typing import List, Tuple

import cv2
import numpy as np


class MaskGenerator:
    """Generates binary masks for Japanese text regions in images."""

    def __init__(self, dilation_pixels: int = 5):
        self.dilation_pixels = dilation_pixels

    def create_mask(self, image_shape: Tuple[int, int, int], bboxes_or_polygons: List[List[float]]) -> np.ndarray:
        h, w = image_shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)

        for region in bboxes_or_polygons:
            if len(region) == 4:  # [x, y, w, h]
                x, y, rw, rh = [int(v) for v in region]
                x1, y1 = max(0, x), max(0, y)
                x2, y2 = min(w, x + rw), min(h, y + rh)
                mask[y1:y2, x1:x2] = 255
            elif len(region) >= 3:  # Polygon points [[x1, y1], [x2, y2], ...]
                pts = np.array(region, dtype=np.int32)
                cv2.fillPoly(mask, [pts], 255)  # type: ignore[list-item]

        if self.dilation_pixels > 0:
            kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT,
                (self.dilation_pixels * 2 + 1, self.dilation_pixels * 2 + 1),
            )
            mask = cv2.dilate(mask, kernel, iterations=1)

        return mask
