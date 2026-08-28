from typing import List, Literal, Optional

from pydantic import BaseModel, Field

SourceType = Literal["pptx_text", "image_text", "table_cell", "notes"]


class RunStyle(BaseModel):
    text: str
    font_name: Optional[str] = None
    font_size: Optional[float] = None  # Pt
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    color: Optional[str] = None  # Hex color code like "#222222"
    hyperlink: Optional[str] = None


class ElementStyle(BaseModel):
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    color: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    alignment: Optional[str] = None


class TextElement(BaseModel):
    element_id: str
    slide_index: int  # 0-indexed slide index
    source_type: SourceType
    source_text: str
    translation: Optional[str] = None
    bbox: Optional[List[float]] = None  # [left, top, width, height] in EMU or pt
    style: ElementStyle = Field(default_factory=ElementStyle)

    # Specific for PPTX Text
    shape_id: Optional[int] = None
    paragraph_index: Optional[int] = None
    cell_address: Optional[List[int]] = None  # [row, col] for table
    runs: List[RunStyle] = Field(default_factory=list)
    bullet_level: int = 0

    # Specific for Image Text
    parent_image_id: Optional[str] = None
    bbox_in_image: Optional[List[float]] = None  # [x, y, w, h] in pixels
    ocr_confidence: Optional[float] = None
    polygon: Optional[List[List[float]]] = None

    # Classification & Status
    is_translatable: bool = True
    skip_reason: Optional[str] = None
