from __future__ import annotations

from pathlib import Path

import dokuma


def test_inspect_xls_reports_sheets(sample_xls: Path) -> None:
    info = dokuma.inspect(sample_xls)

    assert info.format == "xls"
    assert info.size_bytes == sample_xls.stat().st_size
    assert info.sheet_count == 2
    assert info.sheet_names == ["Data", "Notes"]
    assert info.page_count is None


def test_inspect_xls_reports_dimensions(sample_xls: Path) -> None:
    info = dokuma.inspect(sample_xls)

    assert info.sheet_dimensions["Data"] == "A1:B2"


def test_inspect_xls_has_no_title_or_metadata(sample_xls: Path) -> None:
    # Documented, real limitation: xlrd doesn't parse the OLE
    # SummaryInformation stream where .xls stores workbook metadata.
    info = dokuma.inspect(sample_xls)
    assert info.title is None
    assert info.metadata == {}
