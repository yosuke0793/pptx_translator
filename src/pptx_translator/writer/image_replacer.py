import logging
from typing import Any, Dict

from pptx.enum.shapes import MSO_SHAPE_TYPE

logger = logging.getLogger(__name__)


class ImageReplacer:
    """Replaces picture elements in PPTX slides with cleaned images."""

    def replace_images(self, prs: Any, cleaned_images: Dict[str, bytes]) -> Any:
        """cleaned_images: Map of image_id -> cleaned_image_bytes"""
        for slide_idx, slide in enumerate(prs.slides):
            for shape in slide.shapes:
                self._process_shape(shape, slide_idx, cleaned_images)
        return prs

    def _process_shape(self, shape, slide_idx: int, cleaned_images: Dict[str, bytes]) -> None:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            for sub_shape in shape.shapes:
                self._process_shape(sub_shape, slide_idx, cleaned_images)
            return

        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE or (
            hasattr(shape, "image") and shape.image is not None
        ):
            shape_id = shape.shape_id if hasattr(shape, "shape_id") else 0
            image_id = f"slide_{slide_idx+1}_image_{shape_id}"

            if image_id in cleaned_images:
                try:
                    cleaned_bytes = cleaned_images[image_id]
                    # Update image part blob in pptx
                    shape.image._blob = cleaned_bytes
                    logger.info(f"Replaced image blob for {image_id}")
                except Exception as e:
                    logger.warning(f"Failed to replace image blob for {image_id}: {e}")
