import hashlib
import json
import os
from typing import Any, Optional


class CacheManager:
    """Manages file-based JSON caching for OCR and translation results."""

    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        self.ocr_cache_dir = os.path.join(cache_dir, "ocr")
        self.trans_cache_dir = os.path.join(cache_dir, "translation")
        os.makedirs(self.ocr_cache_dir, exist_ok=True)
        os.makedirs(self.trans_cache_dir, exist_ok=True)

    def get_ocr(self, image_hash: str, config_hash: str = "") -> Optional[Any]:
        key = hashlib.sha256(f"{image_hash}:{config_hash}".encode()).hexdigest()
        path = os.path.join(self.ocr_cache_dir, f"{key}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def set_ocr(self, image_hash: str, config_hash: str, data: Any) -> None:
        key = hashlib.sha256(f"{image_hash}:{config_hash}".encode()).hexdigest()
        path = os.path.join(self.ocr_cache_dir, f"{key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        key = hashlib.sha256(f"{text}:{source_lang}:{target_lang}".encode()).hexdigest()
        path = os.path.join(self.trans_cache_dir, f"{key}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    return content.get("translation")
            except Exception:
                return None
        return None

    def set_translation(self, text: str, source_lang: str, target_lang: str, translation: str) -> None:
        key = hashlib.sha256(f"{text}:{source_lang}:{target_lang}".encode()).hexdigest()
        path = os.path.join(self.trans_cache_dir, f"{key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"source_text": text, "translation": translation}, f, ensure_ascii=False, indent=2)
