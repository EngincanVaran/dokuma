from __future__ import annotations

from pathlib import Path

import dokuma


def test_inspect_csv_reports_rows_and_columns(sample_csv: Path) -> None:
    info = dokuma.inspect(sample_csv)

    assert info.format == "csv"
    assert info.row_count == 3  # header + 2 data rows
    assert info.column_count == 3
    assert info.metadata["has_header"] == "True"
    assert info.metadata["delimiter"] == ","
    assert info.page_count is None


def test_inspect_tsv_forces_tab_delimiter(sample_tsv: Path) -> None:
    info = dokuma.inspect(sample_tsv)

    # Real bug, fixed: format used to come back "tsv" here, disagreeing
    # with detect_format()/CsvEngine/extract() - all of which treat .tsv
    # as a delimiter variant of "csv", not a separate format. The
    # delimiter (not format) is how a caller tells .csv and .tsv apart.
    assert info.format == "csv"
    assert info.row_count == 3
    assert info.column_count == 3
    # Real bug, fixed: this used to be repr("\t") == "'\\t'" (3 chars,
    # quoted) instead of the raw single-character delimiter - would raise
    # if fed straight back into csv.reader(delimiter=...).
    assert info.metadata["delimiter"] == "\t"
