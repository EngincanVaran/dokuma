from __future__ import annotations

from pathlib import Path

import pytest

import dokuma
from dokuma.detect import UnsupportedFormatError


def test_inspect_pdf_reports_page_count_and_size(sample_pdf: Path) -> None:
    info = dokuma.inspect(sample_pdf)

    assert info.format == "pdf"
    assert info.page_count == 3
    assert info.size_bytes == sample_pdf.stat().st_size
    assert info.size_bytes > 0


def test_inspect_pdf_classifies_as_text_based(sample_pdf: Path) -> None:
    info = dokuma.inspect(sample_pdf)

    assert info.pdf_type == "text_based"
    assert info.needs_ocr() is False


def test_inspect_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        dokuma.inspect("/no/such/file.pdf")


def test_inspect_unsupported_extension_raises(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("hello")

    with pytest.raises(UnsupportedFormatError):
        dokuma.inspect(path)


def test_summary_includes_page_count_and_size(sample_pdf: Path) -> None:
    info = dokuma.inspect(sample_pdf)
    summary = info.summary()

    assert "3" in summary
    assert "pdf" in summary
    assert str(info.size_bytes) not in summary  # size is comma-formatted, not raw
    assert f"{info.size_bytes:,}" in summary
