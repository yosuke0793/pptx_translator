import logging
import os
import shutil
import subprocess
from typing import List

logger = logging.getLogger(__name__)


class SlideRenderer:
    """Renders PPTX slides to preview PNG images using LibreOffice in headless mode."""

    def __init__(self, libreoffice_path: str = "soffice"):
        self.libreoffice_path = libreoffice_path

    def render_previews(self, pptx_path: str, output_dir: str) -> List[str]:
        os.makedirs(output_dir, exist_ok=True)
        lo_bin = shutil.which(self.libreoffice_path) or shutil.which("soffice") or shutil.which("libreoffice")

        if not lo_bin:
            logger.warning(
                f"LibreOffice executable '{self.libreoffice_path}' not found. Slide preview rendering skipped."
            )
            return []

        try:
            # Convert PPTX to PDF via LibreOffice headless
            cmd = [
                lo_bin,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                output_dir,
                pptx_path,
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode != 0:
                logger.warning(f"LibreOffice conversion failed: {res.stderr}")
                return []

            base_name = os.path.splitext(os.path.basename(pptx_path))[0]
            pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

            if not os.path.exists(pdf_path):
                return []

            # If pdf2image is available, convert PDF to PNGs
            rendered_files: List[str] = []
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(pdf_path)
                for idx, img in enumerate(images):
                    img_path = os.path.join(output_dir, f"slide-{idx+1:03d}.png")
                    img.save(img_path, "PNG")
                    rendered_files.append(img_path)
            except Exception as e:
                logger.info(f"pdf2image conversion skipped ({e}). PDF generated at {pdf_path}")
                rendered_files.append(pdf_path)

            return rendered_files
        except Exception as e:
            logger.warning(f"Error during slide rendering: {e}")
            return []
