from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InspectionWarning(BaseModel):
    slide_index: int
    element_id: Optional[str] = None
    warning_type: str  # e.g., "untranslated", "ocr_low_confidence", "overflow", "format_loss", "unsupported_object"
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class InspectionReport(BaseModel):
    total_pptx_texts: int = 0
    total_image_text_regions: int = 0
    added_overlay_textboxes: int = 0
    ocr_low_confidence_count: int = 0
    untranslated_count: int = 0
    unsupported_objects_count: int = 0
    format_loss_count: int = 0
    font_shrink_count: int = 0
    image_inpainting_failures: int = 0
    warnings: List[InspectionWarning] = Field(default_factory=list)
