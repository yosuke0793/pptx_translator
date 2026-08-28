import logging
from typing import Tuple

from pptx_translator.layout.overflow_detector import OverflowDetector
from pptx_translator.models.element import TextElement

logger = logging.getLogger(__name__)


class TextFitter:
    """Adjusts font size, margins, and line breaks to prevent layout overflow."""

    def __init__(self, min_font_size: float = 8.0):
        self.min_font_size = min_font_size
        self.detector = OverflowDetector(min_font_size=min_font_size)

    def fit_element(self, elem: TextElement) -> Tuple[TextElement, bool]:
        """Adjust font size if translation overflows bbox.

        Returns (updated_element, hit_min_font_size_warning).
        """
        if not elem.translation or not elem.bbox:
            return elem, False

        current_size = elem.style.font_size or 12.0
        is_overflow, suggested_size = self.detector.estimate_text_overflow(
            elem.translation, current_size, elem.bbox
        )

        hit_warning = False
        if is_overflow:
            if suggested_size < self.min_font_size:
                elem.style.font_size = self.min_font_size
                hit_warning = True
            else:
                elem.style.font_size = round(suggested_size, 1)

        return elem, hit_warning
