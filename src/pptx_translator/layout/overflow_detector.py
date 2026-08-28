from typing import List, Tuple


class OverflowDetector:
    """Detects text overflow and overlap in slide elements."""

    def __init__(self, min_font_size: float = 8.0):
        self.min_font_size = min_font_size

    def estimate_text_overflow(self, text: str, font_size: float, bbox: List[float]) -> Tuple[bool, float]:
        """Estimate if text exceeds bbox area.

        Returns (is_overflow, suggested_font_size).
        """
        if not bbox or len(bbox) < 4 or bbox[2] <= 0 or bbox[3] <= 0:
            return False, font_size

        width_pt = bbox[2] / 12700.0 if bbox[2] > 1000 else bbox[2]
        height_pt = bbox[3] / 12700.0 if bbox[3] > 1000 else bbox[3]

        # Rough character estimation per line for English text
        char_width_pt = font_size * 0.5
        chars_per_line = max(1.0, width_pt / char_width_pt)
        estimated_lines = max(1.0, len(text) / chars_per_line)
        required_height_pt = estimated_lines * (font_size * 1.2)

        if required_height_pt > height_pt:
            # Calculate suggested font size to fit
            suggested = max(self.min_font_size, font_size * (height_pt / required_height_pt))
            return True, suggested

        return False, font_size
