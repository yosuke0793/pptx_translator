import os
import tempfile

from pptx_translator.cache.cache_manager import CacheManager
from pptx_translator.models.element import TextElement
from pptx_translator.models.slide import IntermediateRepresentation, SlideModel
from pptx_translator.translation.consistency_checker import ConsistencyChecker
from pptx_translator.translation.glossary import Glossary
from pptx_translator.translation.llm_provider import LLMProvider


def test_glossary():
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write("terms:\n  均質化解析: homogenization analysis\nprotected_terms:\n  - FFT\n")
        f_path = f.name

    try:
        glossary = Glossary.load_from_yaml(f_path)
        assert glossary.terms["均質化解析"] == "homogenization analysis"
        assert "FFT" in glossary.protected_terms

        applied = glossary.apply_post_translation("This is 均質化解析")
        assert "homogenization analysis" in applied
    finally:
        os.remove(f_path)


def test_consistency_checker():
    glossary = Glossary(protected_terms=["FFT"])
    checker = ConsistencyChecker(glossary)

    ir = IntermediateRepresentation(
        slides=[
            SlideModel(
                slide_index=0,
                slide_id=1,
                elements=[
                    TextElement(
                        element_id="elem_1",
                        slide_index=0,
                        source_type="pptx_text",
                        source_text="FFT解析",
                        translation="Fast Fourier Transform Analysis",  # Modified FFT to full name
                    )
                ],
            )
        ]
    )

    warnings = checker.check(ir)
    assert len(warnings) == 1
    assert "FFT" in warnings[0].message


def test_llm_provider_fallback_without_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(cache_dir=tmpdir)
        provider = LLMProvider(api_key=None, cache_manager=cache)

        ir = IntermediateRepresentation(
            slides=[
                SlideModel(
                    slide_index=0,
                    slide_id=1,
                    elements=[
                        TextElement(
                            element_id="elem_1",
                            slide_index=0,
                            source_type="pptx_text",
                            source_text="概要",
                        )
                    ],
                )
            ]
        )

        ir = provider.translate_all(ir)
        assert ir.slides[0].elements[0].translation == "[EN] 概要"
