import os
from typing import Dict, List, Optional

import yaml


class Glossary:
    """Manages terms dictionary and protected terms from YAML file."""

    def __init__(self, terms: Optional[Dict[str, str]] = None, protected_terms: Optional[List[str]] = None):
        self.terms = terms or {}
        self.protected_terms = protected_terms or []

    @classmethod
    def load_from_yaml(cls, yaml_path: str) -> "Glossary":
        if not os.path.exists(yaml_path):
            return cls()
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            terms=data.get("terms", {}),
            protected_terms=data.get("protected_terms", []),
        )

    def apply_pre_translation(self, text: str) -> str:
        """Apply glossary terms before LLM translation if needed."""
        return text

    def apply_post_translation(self, text: str) -> str:
        """Enforce glossary translations on target text."""
        result = text
        for jp, en in self.terms.items():
            # If original contained the term, try to align
            if jp in result:
                result = result.replace(jp, en)
        return result
