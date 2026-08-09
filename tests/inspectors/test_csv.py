from __future__ import annotations

from pathlib import Path

import dokuma


def test_inspect_csv_reports_rows_and_columns(sample_csv: Path) -> None:
    info = dokuma.inspect(sample_csv)

    assert info.format == "csv"
    assert info.row_count == 3  # header + 2 data rows
    assert info.column_count == 3
    assert info.metadata["has_header"] == "True"
    assert info.page_count is None


def test_inspect_tsv_forces_tab_delimiter(sample_tsv: Path) -> None:
    info = dokuma.inspect(sample_tsv)

    assert info.format == "tsv"
    assert info.row_count == 3
    assert info.column_count == 3
    assert info.metadata["delimiter"] == repr("\t")
