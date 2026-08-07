from __future__ import annotations

from pathlib import Path

from dokuma.engines.xlsx import XlsxEngine


def test_xlsx_engine_one_table_region_per_sheet(sample_xlsx: Path) -> None:
    # sample_xlsx (conftest.py) has two sheets with data: "Data", "Notes".
    result = XlsxEngine().extract(sample_xlsx)

    assert result.error is None
    assert result.engine == "openpyxl"
    assert [r.category for r in result.regions] == ["table", "table"]
    assert [r.page for r in result.regions] == [1, 2]
    assert [r.order for r in result.regions] == [0, 1]


def test_xlsx_engine_table_content(sample_xlsx: Path) -> None:
    result = XlsxEngine().extract(sample_xlsx)

    data_table, notes_table = result.tables
    assert "Name" in data_table
    assert "widgets" in data_table
    assert "42" in data_table
    assert "just a note" in notes_table


def test_xlsx_engine_no_bbox(sample_xlsx: Path) -> None:
    result = XlsxEngine().extract(sample_xlsx)
    assert all(r.bbox is None for r in result.regions)


def test_xlsx_engine_skips_empty_sheets(tmp_path: Path) -> None:
    import openpyxl

    workbook = openpyxl.Workbook()
    workbook.active.title = "HasData"
    workbook.active["A1"] = "content"
    workbook.create_sheet("Empty")
    path = tmp_path / "with_empty_sheet.xlsx"
    workbook.save(str(path))

    result = XlsxEngine().extract(path)

    assert len(result.regions) == 1
    assert "content" in result.tables[0]


def test_xlsx_engine_rejects_non_xlsx_file(dense_text_pdf: Path) -> None:
    result = XlsxEngine().extract(dense_text_pdf)

    assert result.error is not None
    assert "xlsx" in result.error
    assert "pdf" in result.error
