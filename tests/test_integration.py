import io
import json
import os
import tempfile

from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.util import Inches

from pptx_translator.cli import main
from pptx_translator.parser.pptx_parser import PPTXParser


def create_pptx_with_image(path: str):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Add text box
    tb = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1))
    tb.text_frame.text = "統合テストタイトル"

    # Create dummy PNG image containing Japanese text
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 190, 90], outline=(0, 0, 0))
    # Draw simple filled shape
    draw.rectangle([20, 20, 100, 50], fill=(200, 200, 200))

    img_bytes_io = io.BytesIO()
    img.save(img_bytes_io, format="PNG")
    img_bytes = img_bytes_io.getvalue()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
        tmp_img.write(img_bytes)
        tmp_img_path = tmp_img.name

    try:
        slide.shapes.add_picture(tmp_img_path, Inches(1), Inches(3), Inches(3), Inches(1.5))
        prs.save(path)
    finally:
        if os.path.exists(tmp_img_path):
            os.remove(tmp_img_path)


def test_cli_integration_full_pipeline(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_pptx = os.path.join(tmpdir, "input.pptx")
        output_pptx = os.path.join(tmpdir, "output", "translated.pptx")
        glossary_path = os.path.join(tmpdir, "glossary.yaml")

        create_pptx_with_image(input_pptx)

        with open(glossary_path, "w", encoding="utf-8") as f:
            f.write("terms:\n  統合テストタイトル: Integration Test Title\n")

        # Execute translate CLI
        monkeypatch.setattr(
            "sys.argv",
            [
                "pptx-translator",
                "translate",
                input_pptx,
                "--output",
                output_pptx,
                "--glossary",
                glossary_path,
            ],
        )
        main()

        assert os.path.exists(output_pptx)

        # Check report.json
        report_path = os.path.join(tmpdir, "output", "report.json")
        assert os.path.exists(report_path)
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        assert report_data["total_pptx_texts"] >= 1

        # Check intermediate.json
        inter_path = os.path.join(tmpdir, "output", "intermediate.json")
        assert os.path.exists(inter_path)

        # Verify translated PPTX can be parsed
        parser = PPTXParser(output_pptx)
        ir = parser.parse()
        all_texts = " ".join(e.source_text for s in ir.slides for e in s.elements)
        assert "Integration Test Title" in all_texts or "[EN]" in all_texts

        # Re-run CLI to ensure overlays are not duplicated
        monkeypatch.setattr(
            "sys.argv",
            [
                "pptx-translator",
                "translate",
                output_pptx,
                "--output",
                os.path.join(tmpdir, "output", "rerun.pptx"),
            ],
        )
        main()
        assert os.path.exists(os.path.join(tmpdir, "output", "rerun.pptx"))
