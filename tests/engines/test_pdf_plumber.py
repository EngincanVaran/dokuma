from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from dokuma.config import ExtractConfig
from dokuma.engines.pdf_plumber import PdfPlumberEngine


def test_pdf_plumber_engine_extracts_text_with_real_page_bbox(dense_text_pdf: Path) -> None:
    result = PdfPlumberEngine().extract(dense_text_pdf)

    assert result.error is None
    assert result.engine == "pdfplumber"
    text_regions = [r for r in result.regions if r.category == "text"]
    assert len(text_regions) == 1

    region = text_regions[0]
    assert region.page == 1
    assert region.bbox is not None
    assert region.bbox[2] > 0 and region.bbox[3] > 0  # real page width/height, not None
    assert "real paragraph of test content" in region.content


def test_pdf_plumber_engine_detects_real_table_bbox(table_pdf: Path) -> None:
    result = PdfPlumberEngine().extract(table_pdf)

    assert result.error is None
    table_regions = [r for r in result.regions if r.category == "table"]
    assert len(table_regions) == 1

    table_region = table_regions[0]
    assert table_region.page == 1
    assert table_region.bbox is not None
    # a real, specific bounding box - not (0, 0, page_width, page_height)
    assert table_region.bbox != (0.0, 0.0, 595.28, 841.89)
    assert "widgets" in table_region.content
    assert "<table>" in table_region.content


def test_pdf_plumber_engine_regions_are_ordered_by_position(table_pdf: Path) -> None:
    result = PdfPlumberEngine().extract(table_pdf)

    categories = [r.category for r in result.regions]
    assert categories == ["text", "table"]
    assert [r.order for r in result.regions] == [0, 1]


def test_pdf_plumber_engine_splits_text_around_table_by_real_position(
    text_table_text_pdf: Path,
) -> None:
    # Real bug this locks in: an earlier version emitted "all page text,
    # then all tables" regardless of visual position, which would have put
    # BOTH paragraphs in one text region before the table - wrong reading
    # order whenever a table sits in the middle of a page's content.
    result = PdfPlumberEngine().extract(text_table_text_pdf)

    categories = [r.category for r in result.regions]
    assert categories == ["text", "table", "text"]

    before, table, after = result.regions
    assert "Intro paragraph" in before.content
    assert "Closing paragraph" not in before.content
    assert "Closing paragraph" in after.content
    assert "Intro paragraph" not in after.content
    # each text slice's bbox is a real, distinct vertical range - not both
    # sharing the same (0, 0, width, height) whole-page bbox.
    assert before.bbox is not None
    assert after.bbox is not None
    assert table.bbox is not None
    assert before.bbox != after.bbox
    assert before.bbox[3] <= table.bbox[1]  # before-text ends at/above table top
    assert after.bbox[1] >= table.bbox[3]  # after-text starts at/below table bottom


def test_pdf_plumber_engine_extracts_image_region(image_pdf: Path) -> None:
    result = PdfPlumberEngine().extract(image_pdf)

    assert result.error is None
    image_regions = [r for r in result.regions if r.category == "image"]
    assert len(image_regions) == 1

    region = image_regions[0]
    assert region.page == 1
    assert region.bbox is not None
    assert region.content == ""
    assert region.image_bytes is not None

    # real, decodable PNG bytes - not a placeholder or raw stream data.
    decoded = Image.open(io.BytesIO(region.image_bytes))
    assert decoded.format == "PNG"
    assert decoded.width > 0 and decoded.height > 0


def test_pdf_plumber_engine_splits_text_around_image_by_real_position(image_pdf: Path) -> None:
    result = PdfPlumberEngine().extract(image_pdf)

    categories = [r.category for r in result.regions]
    assert categories == ["text", "image", "text"]

    before, image, after = result.regions
    assert "Intro paragraph" in before.content
    assert "Closing paragraph" in after.content
    assert before.bbox is not None
    assert after.bbox is not None
    assert image.bbox is not None
    assert before.bbox[3] <= image.bbox[1]
    assert after.bbox[1] >= image.bbox[3]


def test_pdf_plumber_engine_orders_text_table_and_image_together(
    table_and_image_pdf: Path,
) -> None:
    result = PdfPlumberEngine().extract(table_and_image_pdf)

    assert result.error is None
    categories = [r.category for r in result.regions]
    assert categories == ["text", "table", "image", "text"]
    assert [r.order for r in result.regions] == [0, 1, 2, 3]


def test_pdf_plumber_engine_images_property_and_save_image(image_pdf: Path, tmp_path: Path) -> None:
    result = PdfPlumberEngine().extract(image_pdf)

    assert len(result.images) == 1
    assert result.images[0] == result.regions[1].image_bytes

    out_path = tmp_path / "extracted.png"
    result.regions[1].save_image(out_path)
    assert Image.open(out_path).format == "PNG"


def test_pdf_plumber_engine_to_markdown_uses_image_placeholder(image_pdf: Path) -> None:
    result = PdfPlumberEngine().extract(image_pdf)
    assert "[image]" in result.to_markdown()


def test_pdf_plumber_engine_flags_needs_ocr_on_pages_with_images(image_pdf: Path) -> None:
    # Verified empirically before writing this (see the module docstring):
    # pdf-inspector's detect_pdf() flags a page as needing OCR whenever it
    # has a substantial embedded image, even with plenty of real
    # surrounding text - image_pdf (real prose before/after a picture) is
    # a real, confirmed trigger for this, not a synthetic edge case.
    result = PdfPlumberEngine().extract(image_pdf)

    assert result.error is None
    assert len(result.regions) == 3
    assert all(r.needs_ocr for r in result.regions)


def test_pdf_plumber_engine_does_not_flag_clean_text_pages(dense_text_pdf: Path) -> None:
    result = PdfPlumberEngine().extract(dense_text_pdf)

    assert result.error is None
    assert len(result.regions) == 1
    assert result.regions[0].needs_ocr is False


def test_pdf_plumber_engine_does_not_flag_table_only_pages(table_pdf: Path) -> None:
    result = PdfPlumberEngine().extract(table_pdf)

    assert result.error is None
    assert all(not r.needs_ocr for r in result.regions)


def test_pdf_plumber_engine_flag_needs_ocr_false_disables_flagging(image_pdf: Path) -> None:
    result = PdfPlumberEngine().extract(image_pdf, config=ExtractConfig(flag_needs_ocr=False))

    assert result.error is None
    assert len(result.regions) == 3
    assert all(not r.needs_ocr for r in result.regions)
