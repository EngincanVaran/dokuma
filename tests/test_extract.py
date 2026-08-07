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


def test_extract_unsupported_format_raises(sample_docx: Path) -> None:
    # docx inspection exists but no extraction engine is wired up yet.
    with pytest.raises(UnsupportedFormatError):
        dokuma.extract(sample_docx)
