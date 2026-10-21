import json
import logging
import os
import urllib.request
from typing import Optional

from pptx_translator.cache.cache_manager import CacheManager
from pptx_translator.models.slide import IntermediateRepresentation, SlideModel
from pptx_translator.translation.base import TranslationProvider
from pptx_translator.translation.glossary import Glossary

logger = logging.getLogger(__name__)


class LLMProvider(TranslationProvider):
    """LLM Translation Provider supporting OpenAI Chat Completions API and Google Gemini API with caching and glossary."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        target_lang: str = "en",
        glossary: Optional[Glossary] = None,
        cache_manager: Optional[CacheManager] = None,
        backend: str = "openai",
    ):
        self.backend = backend
        if api_key:
            self.api_key = api_key
        elif backend == "gemini":
            self.api_key = os.environ.get("GEMINI_NPI_KEY") or os.environ.get("GEMINI_API_KEY")
        else:
            self.api_key = os.environ.get("OPENAI_API_KEY")
        self.model = model or ("gemini-2.5-flash" if backend == "gemini" else "gpt-4o-mini")
        self.target_lang = target_lang
        self.glossary = glossary or Glossary()
        self.cache_manager = cache_manager or CacheManager()

    def translate_slide(self, slide: SlideModel, context: IntermediateRepresentation) -> SlideModel:
        # Filter translatable elements without translation
        trans_elements = [
            elem for elem in slide.elements if elem.is_translatable and not elem.translation
        ]
        if not trans_elements:
            return slide

        # 1. Try cache first for each element
        to_translate = []
        for elem in trans_elements:
            cached = self.cache_manager.get_translation(elem.source_text, "ja", self.target_lang)
            if cached:
                elem.translation = self.glossary.apply_post_translation(cached)
            else:
                to_translate.append(elem)

        if not to_translate:
            return slide

        # 2. Call LLM API if key is available
        if not self.api_key:
            env_hint = "GEMINI_NPI_KEY / GEMINI_API_KEY" if self.backend == "gemini" else "OPENAI_API_KEY"
            logger.warning(f"No API key found ({env_hint}). Falling back to dummy translation prefix.")
            for elem in to_translate:
                elem.translation = f"[EN] {elem.source_text}"
            return slide

        payload_items = [
            {"id": elem.element_id, "text": elem.source_text} for elem in to_translate
        ]

        system_prompt = (
            f"You are a professional translator translating Japanese PowerPoint slides to {self.target_lang}.\n"
            "Maintain concise slide-style phrasing. Preserve formatting codes or variables.\n"
            "Return JSON matching: {\"translations\": [{\"id\": \"...\", \"translation\": \"...\"}]}"
        )
        if self.glossary.terms:
            system_prompt += f"\nGlossary: {json.dumps(self.glossary.terms, ensure_ascii=False)}"
        if self.glossary.protected_terms:
            system_prompt += f"\nDo NOT translate these protected terms: {json.dumps(self.glossary.protected_terms, ensure_ascii=False)}"

        user_content = json.dumps({"presentation_title": context.title, "slide_title": slide.title, "items": payload_items}, ensure_ascii=False)

        try:
            if self.backend == "gemini":
                trans_map = self._call_gemini(system_prompt, user_content)
            else:
                trans_map = self._call_openai(system_prompt, user_content)

            for elem in to_translate:
                if elem.element_id in trans_map:
                    trans_text = self.glossary.apply_post_translation(trans_map[elem.element_id])
                    elem.translation = trans_text
                    self.cache_manager.set_translation(elem.source_text, "ja", self.target_lang, trans_text)
                else:
                    elem.translation = f"[EN] {elem.source_text}"
        except Exception as e:
            logger.error(f"LLM API translation failed: {e}. Falling back to default.")
            for elem in to_translate:
                elem.translation = f"[EN] {elem.source_text}"

        return slide

    def _call_openai(self, system_prompt: str, user_content: str) -> dict:
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps({
                "model": self.model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.3,
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result_json = json.loads(resp.read().decode("utf-8"))
            content = result_json["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return {item["id"]: item["translation"] for item in parsed.get("translations", []) if "id" in item and "translation" in item}

    def _call_gemini(self, system_prompt: str, user_content: str) -> dict:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        req = urllib.request.Request(
            url,
            data=json.dumps({
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_content}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "response_mime_type": "application/json",
                },
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result_json = json.loads(resp.read().decode("utf-8"))
            content = result_json["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content)
            return {item["id"]: item["translation"] for item in parsed.get("translations", []) if "id" in item and "translation" in item}

    def translate_all(self, ir: IntermediateRepresentation) -> IntermediateRepresentation:
        for slide in ir.slides:
            self.translate_slide(slide, ir)
        return ir
