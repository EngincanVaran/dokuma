from __future__ import annotations

from pathlib import Path

import dokuma


def test_inspect_xlsx_reports_sheets(sample_xlsx: Path) -> None:
    info = dokuma.inspect(sample_xlsx)

    assert info.format == "xlsx"
    assert info.size_bytes == sample_xlsx.stat().st_size
    assert info.sheet_count == 2
    assert info.sheet_names == ["Data", "Notes"]
    assert info.page_count is None  # xlsx has no page concept


def test_inspect_xlsx_reports_dimensions(sample_xlsx: Path) -> None:
    info = dokuma.inspect(sample_xlsx)

    assert info.sheet_dimensions["Data"] == "A1:B2"


def test_inspect_xlsx_reads_properties(sample_xlsx: Path) -> None:
    info = dokuma.inspect(sample_xlsx)

    assert info.title == "Dokuma Test Workbook"
    assert info.metadata.get("creator") == "dokuma"
