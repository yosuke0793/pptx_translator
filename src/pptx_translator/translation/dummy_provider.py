from pptx_translator.models.slide import IntermediateRepresentation, SlideModel
from pptx_translator.translation.base import TranslationProvider


class DummyProvider(TranslationProvider):
    """Deterministic dummy translation provider for testing and offline execution."""

    def __init__(self, prefix: str = "[EN] "):
        self.prefix = prefix

    def translate_text(self, text: str) -> str:
        if not text:
            return text
        # Simple sample replacements for common terms if needed, otherwise prefix
        replacements = {
            "概要": "Overview",
            "解析結果": "Analysis Results",
            "応力分布": "Stress Distribution",
            "結論": "Conclusion",
            "表": "Table",
            "タイトル": "Title",
        }
        for jp, en in replacements.items():
            text = text.replace(jp, en)
        return f"{self.prefix}{text}"

    def translate_slide(self, slide: SlideModel, context: IntermediateRepresentation) -> SlideModel:
        for elem in slide.elements:
            if elem.is_translatable and elem.translation is None:
                elem.translation = self.translate_text(elem.source_text)
        return slide

    def translate_all(self, ir: IntermediateRepresentation) -> IntermediateRepresentation:
        for slide in ir.slides:
            self.translate_slide(slide, ir)
        return ir
