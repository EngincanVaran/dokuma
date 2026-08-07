from __future__ import annotations

from pathlib import Path

import pytest

import dokuma
from dokuma.config import ExtractConfig


def test_extract_config_defaults_to_html() -> None:
    assert ExtractConfig().table_format == "html"


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
