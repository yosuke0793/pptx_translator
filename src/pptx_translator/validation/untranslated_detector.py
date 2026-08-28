from typing import List

from pptx_translator.models.inspection import InspectionWarning
from pptx_translator.models.slide import IntermediateRepresentation
from pptx_translator.parser.text_run_merger import has_japanese


class UntranslatedDetector:
    """Detects untranslated Japanese text in translated presentation elements."""

    def detect(self, ir: IntermediateRepresentation) -> List[InspectionWarning]:
        warnings: List[InspectionWarning] = []

        for slide in ir.slides:
            for elem in slide.elements:
                if not elem.is_translatable:
                    continue

                text_to_check = elem.translation or elem.source_text
                if has_japanese(text_to_check):
                    warnings.append(
                        InspectionWarning(
                            slide_index=slide.slide_index,
                            element_id=elem.element_id,
                            warning_type="untranslated",
                            message=f"Untranslated Japanese text detected in {elem.element_id}: '{text_to_check}'",
                        )
                    )

        return warnings
