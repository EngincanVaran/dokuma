from __future__ import annotations

from pathlib import Path

import pytest

import dokuma
from dokuma.detect import UnsupportedFormatError
from dokuma.engines.pdf_inspector import PdfInspectorEngine


def test_extract_pdf_dispatches_to_default_engine(dense_text_pdf: Path) -> None:
    result = dokuma.extract(dense_text_pdf)

    assert result.engine == "pdf-inspector"
    assert result.error is None
    assert "real paragraph of test content" in result.text


def test_extract_accepts_explicit_engine(dense_text_pdf: Path) -> None:
    result = dokuma.extract(dense_text_pdf, engine=PdfInspectorEngine())
    assert result.engine == "pdf-inspector"


def test_extract_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        dokuma.extract("/no/such/file.pdf")


def test_extract_docx_dispatches_to_default_engine(sample_docx: Path) -> None:
    result = dokuma.extract(sample_docx)

    assert result.engine == "python-docx"
    assert result.error is None
    assert "Introduction" in result.text


def test_extract_xlsx_dispatches_to_default_engine(sample_xlsx: Path) -> None:
    result = dokuma.extract(sample_xlsx)

    assert result.engine == "openpyxl"
    assert result.error is None
    # xlsx has no "text" content - every region is a "table" (each sheet).
    assert any("widgets" in table for table in result.tables)


def test_extract_html_dispatches_to_default_engine(sample_html: Path) -> None:
    result = dokuma.extract(sample_html)

    assert result.engine == "html.parser"
    assert result.error is None
    assert "Welcome" in result.text


def test_extract_markdown_dispatches_to_default_engine(sample_markdown: Path) -> None:
    result = dokuma.extract(sample_markdown)

    assert result.engine == "markdown"
    assert result.error is None
    assert "Dokuma Test Doc" in result.text


def test_extract_xls_dispatches_to_default_engine(sample_xls: Path) -> None:
    result = dokuma.extract(sample_xls)

    assert result.engine == "xlrd"
    assert result.error is None
    assert any("widgets" in table for table in result.tables)


def test_extract_csv_dispatches_to_default_engine(sample_csv: Path) -> None:
    result = dokuma.extract(sample_csv)

    assert result.engine == "csv"
    assert result.error is None
    assert any("widgets" in table for table in result.tables)


def test_extract_email_dispatches_to_default_engine(sample_eml: Path) -> None:
    result = dokuma.extract(sample_eml)

    assert result.engine == "email"
    assert result.error is None
    assert "body of the test email" in result.text


def test_extract_unsupported_format_raises(tmp_path: Path) -> None:
    path = tmp_path / "sample.exe"
    path.write_text("irrelevant")

    with pytest.raises(UnsupportedFormatError):
        dokuma.extract(path)
