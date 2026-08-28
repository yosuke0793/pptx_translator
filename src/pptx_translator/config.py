from typing import Optional

import yaml
from pydantic import BaseModel


class Config(BaseModel):
    provider: str = "dummy"
    model: Optional[str] = None
    api_key: Optional[str] = None
    ocr_lang: str = "japan"
    ocr_confidence_threshold: float = 0.90
    ocr_low_confidence_action: str = "warn"  # "warn", "skip", "replace"
    min_font_size: float = 8.0
    inpainting_method: str = "telea"  # "telea", "ns", "solid"
    translate_notes: bool = True
    target_lang: str = "en"
    cache_dir: str = ".cache"
    libreoffice_path: str = "soffice"
    log_level: str = "INFO"

    @classmethod
    def load_from_yaml(cls, yaml_path: str) -> "Config":
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)
