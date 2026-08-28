from typing import List

from pptx_translator.ocr.detector import OCRResultItem


class TextGrouper:
    """Group neighboring OCR items into horizontal text lines or blocks."""

    def __init__(self, horizontal_margin_ratio: float = 0.5, vertical_overlap_threshold: float = 0.5):
        self.horizontal_margin_ratio = horizontal_margin_ratio
        self.vertical_overlap_threshold = vertical_overlap_threshold

    def group(self, items: List[OCRResultItem]) -> List[OCRResultItem]:
        if not items:
            return []

        # Sort items primarily by Y coordinate, secondarily by X coordinate
        sorted_items = sorted(items, key=lambda item: (item.bbox[1], item.bbox[0]))
        lines: List[List[OCRResultItem]] = []

        for item in sorted_items:
            placed = False
            for line in lines:
                ref_item = line[0]
                # Check vertical overlap
                y1 = max(item.bbox[1], ref_item.bbox[1])
                y2 = min(item.bbox[1] + item.bbox[3], ref_item.bbox[1] + ref_item.bbox[3])
                overlap = max(0.0, y2 - y1)
                min_height = min(item.bbox[3], ref_item.bbox[3])

                if min_height > 0 and (overlap / min_height) >= self.vertical_overlap_threshold:
                    line.append(item)
                    placed = True
                    break

            if not placed:
                lines.append([item])

        # Merge each line into a combined OCRResultItem
        grouped: List[OCRResultItem] = []
        for line in lines:
            line_sorted = sorted(line, key=lambda it: it.bbox[0])
            combined_text = " ".join(it.text for it in line_sorted)

            min_x = min(it.bbox[0] for it in line_sorted)
            min_y = min(it.bbox[1] for it in line_sorted)
            max_r = max(it.bbox[0] + it.bbox[2] for it in line_sorted)
            max_b = max(it.bbox[1] + it.bbox[3] for it in line_sorted)

            combined_bbox = [min_x, min_y, max_r - min_x, max_b - min_y]
            avg_conf = sum(it.confidence for it in line_sorted) / len(line_sorted)
            poly = [
                [min_x, min_y],
                [max_r, min_x],
                [max_r, max_b],
                [min_x, max_b],
            ]

            grouped.append(
                OCRResultItem(
                    text=combined_text,
                    bbox=combined_bbox,
                    polygon=poly,
                    confidence=avg_conf,
                    text_color=line_sorted[0].text_color,
                    background_color=line_sorted[0].background_color,
                )
            )

        return grouped
