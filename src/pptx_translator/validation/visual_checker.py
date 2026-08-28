from typing import List

from pptx_translator.layout.text_fitter import TextFitter
from pptx_translator.models.inspection import InspectionReport, InspectionWarning
from pptx_translator.models.slide import IntermediateRepresentation
from pptx_translator.validation.untranslated_detector import UntranslatedDetector


class VisualChecker:
    """Aggregates layout, overflow, untranslated, and OCR confidence checks into InspectionReport."""

    def __init__(self, min_font_size: float = 8.0, ocr_confidence_threshold: float = 0.90):
        self.min_font_size = min_font_size
        self.ocr_confidence_threshold = ocr_confidence_threshold
        self.untranslated_detector = UntranslatedDetector()
        self.text_fitter = TextFitter(min_font_size=min_font_size)

    def validate(self, ir: IntermediateRepresentation) -> InspectionReport:
        report = InspectionReport()
        warnings: List[InspectionWarning] = []

        total_pptx_texts = 0
        total_image_text_regions = 0
        added_overlays = 0
        low_conf_count = 0

        # Check elements
        for slide in ir.slides:
            for elem in slide.elements:
                if elem.source_type in ("pptx_text", "table_cell", "notes"):
                    total_pptx_texts += 1
                elif elem.source_type == "image_text":
                    total_image_text_regions += 1
                    if elem.translation:
                        added_overlays += 1

                # Check OCR confidence
                if elem.ocr_confidence is not None and elem.ocr_confidence < self.ocr_confidence_threshold:
                    low_conf_count += 1
                    warnings.append(
                        InspectionWarning(
                            slide_index=slide.slide_index,
                            element_id=elem.element_id,
                            warning_type="ocr_low_confidence",
                            message=f"OCR confidence ({elem.ocr_confidence:.2f}) below threshold ({self.ocr_confidence_threshold:.2f})",
                        )
                    )

                # Check layout overflow & fit
                if elem.translation:
                    _, hit_min_font_warning = self.text_fitter.fit_element(elem)
                    if hit_min_font_warning:
                        report.font_shrink_count += 1
                        warnings.append(
                            InspectionWarning(
                                slide_index=slide.slide_index,
                                element_id=elem.element_id,
                                warning_type="overflow",
                                message=f"Font size reached minimum constraint ({self.min_font_size} pt) for text '{elem.translation}'",
                            )
                        )

        # Check untranslated
        untranslated_warnings = self.untranslated_detector.detect(ir)
        warnings.extend(untranslated_warnings)

        report.total_pptx_texts = total_pptx_texts
        report.total_image_text_regions = total_image_text_regions
        report.added_overlay_textboxes = added_overlays
        report.ocr_low_confidence_count = low_conf_count
        report.untranslated_count = len(untranslated_warnings)
        report.warnings = warnings

        return report
