import argparse
import io
import logging
import os
from typing import Dict

import numpy as np
from PIL import Image

from pptx_translator.cache.cache_manager import CacheManager
from pptx_translator.config import Config
from pptx_translator.image_processing.background_cleaner import BackgroundCleaner
from pptx_translator.image_processing.mask_generator import MaskGenerator
from pptx_translator.parser.image_extractor import ImageExtractor
from pptx_translator.parser.pptx_parser import PPTXParser
from pptx_translator.translation.consistency_checker import ConsistencyChecker
from pptx_translator.translation.dummy_provider import DummyProvider
from pptx_translator.translation.glossary import Glossary
from pptx_translator.translation.llm_provider import LLMProvider
from pptx_translator.validation.slide_renderer import SlideRenderer
from pptx_translator.validation.visual_checker import VisualChecker
from pptx_translator.writer.image_replacer import ImageReplacer
from pptx_translator.writer.overlay_text_writer import OverlayTextWriter
from pptx_translator.writer.text_replacer import TextReplacer


def setup_logging(level_name: str = "INFO"):
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def cmd_translate(args):
    config = Config.load_from_yaml(args.config) if args.config and os.path.exists(args.config) else Config()
    setup_logging(config.log_level)
    logger = logging.getLogger(__name__)

    glossary = Glossary.load_from_yaml(args.glossary) if args.glossary else Glossary()
    cache_manager = CacheManager(cache_dir=config.cache_dir)

    logger.info(f"Parsing PPTX: {args.input}")
    parser = PPTXParser(
        pptx_path=args.input,
        translate_notes=config.translate_notes,
        ocr_lang=config.ocr_lang,
        ocr_confidence_threshold=config.ocr_confidence_threshold,
        cache_manager=cache_manager,
    )
    ir = parser.parse()

    # Provider selection
    if config.provider == "gemini":
        provider = LLMProvider(
            api_key=config.api_key,
            model=config.model or "gemini-2.5-flash",
            target_lang=config.target_lang,
            glossary=glossary,
            cache_manager=cache_manager,
            backend="gemini",
        )
    elif config.provider == "llm" or config.provider == "openai":
        provider = LLMProvider(
            api_key=config.api_key,
            model=config.model or "gpt-4o-mini",
            target_lang=config.target_lang,
            glossary=glossary,
            cache_manager=cache_manager,
            backend="openai",
        )
    else:
        provider = DummyProvider()

    ir = provider.translate_all(ir)

    # Consistency check
    consistency_checker = ConsistencyChecker(glossary)
    consistency_warnings = consistency_checker.check(ir)

    # Outputs setup
    output_pptx = args.output if args.output else "output/translated.pptx"
    output_dir = os.path.dirname(output_pptx) or "output"
    os.makedirs(output_dir, exist_ok=True)

    cleaned_img_dir = os.path.join(output_dir, "cleaned_images")
    os.makedirs(cleaned_img_dir, exist_ok=True)

    # Save intermediate JSON
    intermediate_path = os.path.join(output_dir, "intermediate.json")
    with open(intermediate_path, "w", encoding="utf-8") as f:
        f.write(ir.model_dump_json(indent=2))
    logger.info(f"Saved intermediate representation to {intermediate_path}")

    if args.dry_run:
        logger.info("Dry run complete. No output PPTX will be written.")
        print(f"Extracted {sum(len(s.elements) for s in ir.slides)} elements.")
        return

    # Image cleaning for image_text elements
    mask_gen = MaskGenerator(dilation_pixels=4)
    cleaner = BackgroundCleaner(method=config.inpainting_method)
    image_extractor = ImageExtractor(args.input)

    cleaned_images_map: Dict[str, bytes] = {}

    for slide_model in ir.slides:
        extracted = image_extractor.extract_images_from_slide(parser.prs.slides[slide_model.slide_index], slide_model.slide_index)
        for img_info in extracted:
            img_elems = [
                e for e in slide_model.elements
                if e.source_type == "image_text" and e.parent_image_id == img_info.image_id and e.bbox_in_image
            ]
            if not img_elems:
                continue

            bboxes_or_polys = [e.polygon if e.polygon else e.bbox_in_image for e in img_elems]
            img_pil = Image.open(io.BytesIO(img_info.image_bytes)).convert("RGB")
            img_np = np.array(img_pil)

            mask = mask_gen.create_mask(img_np.shape, bboxes_or_polys)
            cleaned_np = cleaner.clean_image(img_np, mask)

            cleaned_pil = Image.fromarray(cleaned_np)
            buf = io.BytesIO()
            cleaned_pil.save(buf, format="PNG")
            cleaned_bytes = buf.getvalue()

            cleaned_images_map[img_info.image_id] = cleaned_bytes

            # Save cleaned image file
            cleaned_path = os.path.join(cleaned_img_dir, f"{img_info.image_id}.png")
            with open(cleaned_path, "wb") as f:
                f.write(cleaned_bytes)

    # 1. Replace normal PPTX texts
    replacer = TextReplacer(args.input)
    prs = replacer.replace_texts(ir)

    # 2. Replace images with cleaned versions
    image_replacer = ImageReplacer()
    prs = image_replacer.replace_images(prs, cleaned_images_map)

    # 3. Add overlay editable English textboxes
    overlay_writer = OverlayTextWriter()
    prs = overlay_writer.add_overlays(prs, ir)

    prs.save(output_pptx)
    logger.info(f"Saved translated PPTX to {output_pptx}")

    # Validate and generate report
    visual_checker = VisualChecker(
        min_font_size=config.min_font_size,
        ocr_confidence_threshold=config.ocr_confidence_threshold,
    )
    report = visual_checker.validate(ir)
    report.warnings.extend(consistency_warnings)

    report_path = os.path.join(output_dir, "report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))
    logger.info(f"Saved report to {report_path}")

    # Render previews if requested
    preview_dir = os.path.join(output_dir, "preview")
    renderer = SlideRenderer(libreoffice_path=config.libreoffice_path)
    renderer.render_previews(output_pptx, preview_dir)


def cmd_inspect(args):
    parser = PPTXParser(args.input)
    ir = parser.parse()
    output_path = args.output if args.output else "inspection.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ir.model_dump_json(indent=2))
    print(f"Inspected {len(ir.slides)} slides. Output written to {output_path}")


def cmd_render(args):
    output_dir = args.output_dir if args.output_dir else "preview"
    renderer = SlideRenderer()
    files = renderer.render_previews(args.input, output_dir)
    print(f"Rendered {len(files)} preview artifacts to {output_dir}")


def cmd_validate(args):
    parser = PPTXParser(args.input)
    ir = parser.parse()
    visual_checker = VisualChecker()
    report = visual_checker.validate(ir)

    report_path = args.report if args.report else "report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))
    print(f"Validation complete. Total elements: {report.total_pptx_texts + report.total_image_text_regions}. Report saved to {report_path}")


def main():
    parser = argparse.ArgumentParser(prog="pptx-translator", description="PowerPoint Translation CLI Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # translate command
    p_trans = subparsers.add_parser("translate", help="Translate PPTX file")
    p_trans.add_argument("input", help="Input PPTX file path")
    p_trans.add_argument("--output", "-o", help="Output PPTX file path", default="output/translated.pptx")
    p_trans.add_argument("--config", "-c", help="Config YAML file path")
    p_trans.add_argument("--glossary", "-g", help="Glossary YAML file path")
    p_trans.add_argument("--dry-run", action="store_true", help="Perform extraction and translation plan only")
    p_trans.set_defaults(func=cmd_translate)

    # inspect command
    p_insp = subparsers.add_parser("inspect", help="Inspect PPTX and extract text elements to JSON")
    p_insp.add_argument("input", help="Input PPTX file path")
    p_insp.add_argument("--output", "-o", help="Output JSON file path", default="inspection.json")
    p_insp.set_defaults(func=cmd_inspect)

    # render command
    p_ren = subparsers.add_parser("render", help="Render PPTX slides to preview images")
    p_ren.add_argument("input", help="Input PPTX file path")
    p_ren.add_argument("--output-dir", "-o", help="Output preview directory", default="preview/")
    p_ren.set_defaults(func=cmd_render)

    # validate command
    p_val = subparsers.add_parser("validate", help="Validate translated PPTX layout and completeness")
    p_val.add_argument("input", help="Input PPTX file path")
    p_val.add_argument("--report", "-r", help="Output JSON report file path", default="report.json")
    p_val.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
