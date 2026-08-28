import re
from typing import Tuple

from pptx_translator.ocr.detector import OCRResultItem
from pptx_translator.parser.text_run_merger import has_japanese, is_translatable_text

MATH_UNIT_FILENAME_REGEX = re.compile(
    r"^([0-9\.\,\+\-\*\/\=\%\(\)\[\]]+|[a-zA-Z0-9_\-\.]+\.(png|jpg|jpeg|py|cpp|txt|pptx|xlsx)|[0-9]+(px|pt|cm|mm|kg|m|s|V|A|Hz)?)$"
)


class TargetClassifier:
    """Classifies whether OCR items should be translated."""

    def is_target(self, item: OCRResultItem, min_confidence: float = 0.90) -> Tuple[bool, str]:
        text = item.text.strip()
        if not text:
            return False, "empty_text"

        if item.confidence < min_confidence:
            return False, f"low_confidence_{item.confidence:.2f}"

        if MATH_UNIT_FILENAME_REGEX.fullmatch(text):
            return False, "math_unit_filename"

        if not has_japanese(text):
            return False, "no_japanese"

        if not is_translatable_text(text):
            return False, "non_translatable_pattern"

        return True, "valid"
