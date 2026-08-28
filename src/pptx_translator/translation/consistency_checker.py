from typing import List

from pptx_translator.models.inspection import InspectionWarning
from pptx_translator.models.slide import IntermediateRepresentation
from pptx_translator.translation.glossary import Glossary


class ConsistencyChecker:
    """Checks glossary consistency and protected term preservation across presentation."""

    def __init__(self, glossary: Glossary):
        self.glossary = glossary

    def check(self, ir: IntermediateRepresentation) -> List[InspectionWarning]:
        warnings: List[InspectionWarning] = []

        for slide in ir.slides:
            for elem in slide.elements:
                if not elem.is_translatable or not elem.translation:
                    continue

                # Check protected terms
                for pterm in self.glossary.protected_terms:
                    if pterm in elem.source_text and pterm.lower() not in elem.translation.lower():
                        warnings.append(
                            InspectionWarning(
                                slide_index=slide.slide_index,
                                element_id=elem.element_id,
                                warning_type="format_loss",
                                message=f"Protected term '{pterm}' might be missing or modified in translation.",
                            )
                        )

        return warnings
