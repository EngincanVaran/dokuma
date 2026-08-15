from __future__ import annotations

from pathlib import Path

import pytest

import dokuma
from dokuma.config import ExtractConfig


def test_extract_config_defaults_to_html() -> None:
    assert ExtractConfig().table_format == "html"


def test_extract_config_defaults_extract_images_to_true() -> None:
    assert ExtractConfig().extract_images is True


def test_extract_config_defaults_flag_needs_ocr_to_true() -> None:
    assert ExtractConfig().flag_needs_ocr is True


def test_extract_config_rejects_unknown_table_format() -> None:
    with pytest.raises(ValueError, match="not one of"):
        ExtractConfig(table_format="yaml")


def test_extract_respects_table_format_config(table_pdf: Path) -> None:
    result = dokuma.extract(
        table_pdf,
        engine=dokuma.PdfPlumberEngine(),
        config=ExtractConfig(table_format="markdown"),
    )

    assert result.table_format == "markdown"
    assert result.tables[0].startswith("| ")  # markdown pipe table, not <table>


def test_extract_default_table_format_is_html(table_pdf: Path) -> None:
    result = dokuma.extract(table_pdf, engine=dokuma.PdfPlumberEngine())
    assert result.table_format == "html"
    assert result.tables[0].startswith("<table>")


def test_engine_extract_respects_config_on_format_mismatch(dense_text_pdf: Path) -> None:
    # config should still be applied even when extraction fails outright.
    result = dokuma.DocxEngine().extract(dense_text_pdf, config=ExtractConfig(table_format="xml"))
    assert result.error is not None
    assert result.table_format == "xml"


def test_extract_images_true_is_the_default(image_pdf: Path) -> None:
    result = dokuma.extract(image_pdf, engine=dokuma.PdfPlumberEngine())
    assert any(r.category == "image" for r in result.regions)


def test_extract_images_false_skips_pdf_image_regions(image_pdf: Path) -> None:
    result = dokuma.extract(
        image_pdf,
        engine=dokuma.PdfPlumberEngine(),
        config=ExtractConfig(extract_images=False),
    )
    assert result.error is None
    assert not any(r.category == "image" for r in result.regions)
    assert result.images == []


def test_extract_images_false_skips_docx_image_regions(docx_with_image: Path) -> None:
    result = dokuma.extract(
        docx_with_image,
        config=ExtractConfig(extract_images=False),
    )
    assert result.error is None
    assert not any(r.category == "image" for r in result.regions)


def test_extract_images_false_skips_xlsx_image_regions(xlsx_with_image: Path) -> None:
    result = dokuma.extract(
        xlsx_with_image,
        config=ExtractConfig(extract_images=False),
    )
    assert result.error is None
    assert not any(r.category == "image" for r in result.regions)
    # the image-only sheet has nothing left to report once its picture is
    # skipped - it should vanish from the region list entirely, same as
    # any other genuinely empty sheet.
    assert not any(r.page == 2 for r in result.regions)
