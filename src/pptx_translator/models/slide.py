from typing import List, Optional

from pydantic import BaseModel, Field

from pptx_translator.models.element import TextElement


class SlideModel(BaseModel):
    slide_index: int
    slide_id: int
    title: Optional[str] = None
    elements: List[TextElement] = Field(default_factory=list)


class IntermediateRepresentation(BaseModel):
    title: Optional[str] = None
    slides: List[SlideModel] = Field(default_factory=list)
