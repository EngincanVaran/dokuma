from __future__ import annotations

from pathlib import Path

from dokuma.engines.csv import CsvEngine


def test_csv_engine_one_table_region_for_whole_file(sample_csv: Path) -> None:
    result = CsvEngine().extract(sample_csv)

    assert result.error is None
    assert result.engine == "csv"
    assert [r.category for r in result.regions] == ["table"]
    assert result.regions[0].order == 0


def test_csv_engine_table_content_includes_header_and_rows(sample_csv: Path) -> None:
    result = CsvEngine().extract(sample_csv)

    (table,) = result.tables
    assert "name" in table
    assert "widgets" in table
    assert "gadgets" in table


def test_csv_engine_handles_tsv_delimiter(sample_tsv: Path) -> None:
    # sample_tsv (conftest.py) is tab-delimited; the ".tsv" extension is
    # what tells the engine to force a tab delimiter rather than sniff.
    result = CsvEngine().extract(sample_tsv)

    assert result.error is None
    (table,) = result.tables
    assert "widgets" in table
    assert "42" in table


def test_csv_engine_no_bbox_or_page(sample_csv: Path) -> None:
    result = CsvEngine().extract(sample_csv)
    assert all(r.bbox is None for r in result.regions)
    assert all(r.page is None for r in result.regions)


def test_csv_engine_empty_file_has_no_regions(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    result = CsvEngine().extract(path)

    assert result.error is None
    assert result.regions == []


def test_csv_engine_rejects_non_csv_file(dense_text_pdf: Path) -> None:
    result = CsvEngine().extract(dense_text_pdf)

    assert result.error is not None
    assert "csv" in result.error
    assert "pdf" in result.error
