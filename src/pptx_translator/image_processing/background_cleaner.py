import cv2
import numpy as np


class BackgroundCleaner:
    """Removes text from image using mask with inpainting or solid background filling."""

    def __init__(self, method: str = "telea"):
        self.method = method

    def clean_image(self, img_np: np.ndarray, mask: np.ndarray) -> np.ndarray:
        if mask is None or np.count_nonzero(mask) == 0:
            return img_np.copy()

        if self.method == "solid":
            cleaned = img_np.copy()
            # Mean color of non-masked pixels
            non_mask = mask == 0
            if np.any(non_mask):
                avg_color = img_np[non_mask].mean(axis=0)
            else:
                avg_color = [255, 255, 255]
            cleaned[mask > 0] = avg_color
            return cleaned
        elif self.method == "ns":
            return cv2.inpaint(img_np, mask, inpaintRadius=3, flags=cv2.INPAINT_NS)
        else:  # Default TELEA
            return cv2.inpaint(img_np, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
