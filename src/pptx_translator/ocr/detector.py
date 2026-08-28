import io
import logging
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class OCRResultItem:
    def __init__(
        self,
        text: str,
        bbox: List[float],  # [x, y, w, h] in pixels
        polygon: List[List[float]],  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        confidence: float,
        text_color: str = "#000000",
        background_color: str = "#FFFFFF",
    ):
        self.text = text
        self.bbox = bbox
        self.polygon = polygon
        self.confidence = confidence
        self.text_color = text_color
        self.background_color = background_color

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "bbox": self.bbox,
            "polygon": self.polygon,
            "confidence": self.confidence,
            "text_color": self.text_color,
            "background_color": self.background_color,
        }


class OCRDetector:
    """OCR detector supporting PaddleOCR with fallback/mock capabilities."""

    def __init__(self, lang: str = "japan"):
        self.lang = lang
        self._engine: Any = None
        self._engine_type: Optional[str] = None
        self._init_engine()

    def _init_engine(self):
        try:
            from paddleocr import PaddleOCR
            self._engine = PaddleOCR(use_angle_cls=True, lang=self.lang, show_log=False)
            self._engine_type = "paddle"
            logger.info("PaddleOCR engine initialized successfully.")
        except Exception as e:
            logger.warning(f"PaddleOCR failed to initialize ({e}). Falling back to lightweight/mock OCR.")
            self._engine_type = "mock"

    def detect(self, image_bytes: bytes) -> List[OCRResultItem]:
        if self._engine_type == "paddle":
            try:
                img_np = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))
                result = self._engine.ocr(img_np, cls=True)
                items: List[OCRResultItem] = []
                if result and result[0]:
                    for line in result[0]:
                        polygon = line[0]  # [[x1,y1], [x2,y2], ...]
                        text, conf = line[1]
                        xs = [p[0] for p in polygon]
                        ys = [p[1] for p in polygon]
                        min_x, max_x = min(xs), max(xs)
                        min_y, max_y = min(ys), max(ys)
                        bbox = [float(min_x), float(min_y), float(max_x - min_x), float(max_y - min_y)]
                        items.append(
                            OCRResultItem(
                                text=text,
                                bbox=bbox,
                                polygon=polygon,
                                confidence=float(conf),
                            )
                        )
                return items
            except Exception as e:
                logger.warning(f"PaddleOCR detection error: {e}")
                return []
        else:
            # Mock or dummy detection for testing/environments without PaddleOCR
            return []
