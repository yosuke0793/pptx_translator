from typing import Protocol, runtime_checkable

from pptx_translator.models.slide import IntermediateRepresentation, SlideModel


@runtime_checkable
class TranslationProvider(Protocol):
    def translate_slide(self, slide: SlideModel, context: IntermediateRepresentation) -> SlideModel:
        ...

    def translate_all(self, ir: IntermediateRepresentation) -> IntermediateRepresentation:
        ...
