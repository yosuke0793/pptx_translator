import re
from typing import Any, List, Optional, Tuple

from pptx_translator.models.element import ElementStyle, RunStyle

# REGEX Patterns for non-translatable text
URL_REGEX = re.compile(r"https?://\S+|www\.\S+")
EMAIL_REGEX = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
NUMERIC_CODE_REGEX = re.compile(r"^[0-9\s\.\,\+\-\*\/\=\%\:\;\_]+$")


def has_japanese(text: str) -> bool:
    """Check if the text contains Japanese characters (Hiragana, Katakana, Kanji)."""
    # Hiragana: \u3040-\u309F, Katakana: \u30A0-\u30FF, Kanji: \u4E00-\u9FFF
    pattern = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]")
    return bool(pattern.search(text))


def is_translatable_text(text: str) -> bool:
    """Determine if a text should be translated."""
    stripped = text.strip()
    if not stripped:
        return False

    # Check for pure URLs, emails, numbers/code
    if URL_REGEX.fullmatch(stripped):
        return False
    if EMAIL_REGEX.fullmatch(stripped):
        return False
    if NUMERIC_CODE_REGEX.fullmatch(stripped):
        return False

    # Default rule: translate if contains Japanese
    return has_japanese(stripped)


def rgb_to_hex(rgb_color) -> Optional[str]:
    """Convert RGBColor to Hex string."""
    try:
        return f"#{rgb_color.r:02X}{rgb_color.g:02X}{rgb_color.b:02X}"
    except Exception:
        return None


def extract_run_style(run: Any) -> RunStyle:
    font_name = run.font.name
    font_size = run.font.size.pt if run.font.size else None
    bold = run.font.bold
    italic = run.font.italic
    color = rgb_to_hex(run.font.color.rgb) if (hasattr(run.font, "color") and run.font.color and hasattr(run.font.color, "rgb") and run.font.color.rgb) else None
    hyperlink = run.hyperlink.address if hasattr(run, "hyperlink") and run.hyperlink else None

    return RunStyle(
        text=run.text,
        font_name=font_name,
        font_size=font_size,
        bold=bold,
        italic=italic,
        color=color,
        hyperlink=hyperlink,
    )


def get_dominant_style(runs_info: List[RunStyle]) -> ElementStyle:
    """Extract dominant style from runs."""
    if not runs_info:
        return ElementStyle()

    # Find font_name, font_size, bold, color by frequency/presence
    font_names = [r.font_name for r in runs_info if r.font_name]
    font_sizes = [r.font_size for r in runs_info if r.font_size is not None]
    bolds = [r.bold for r in runs_info if r.bold is not None]
    colors = [r.color for r in runs_info if r.color]

    dominant_font = max(set(font_names), key=font_names.count) if font_names else None
    dominant_size = font_sizes[0] if font_sizes else None
    dominant_bold = any(bolds) if bolds else None
    dominant_color = colors[0] if colors else None

    return ElementStyle(
        font_name=dominant_font,
        font_size=dominant_size,
        bold=dominant_bold,
        color=dominant_color,
    )


def merge_paragraph_runs(paragraph: Any) -> Tuple[str, List[RunStyle], ElementStyle]:
    """Merge paragraph runs into full text, keeping run details and dominant style."""
    full_text = "".join(r.text for r in paragraph.runs) if paragraph.runs else paragraph.text
    runs_info = [extract_run_style(r) for r in paragraph.runs]
    style = get_dominant_style(runs_info)
    return full_text, runs_info, style
