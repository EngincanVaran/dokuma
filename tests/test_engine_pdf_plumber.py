from __future__ import annotations

from pathlib import Path

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
