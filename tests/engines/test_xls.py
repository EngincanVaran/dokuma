from __future__ import annotations

from pathlib import Path

from dokuma.engines.xls import XlsEngine


def test_xls_engine_one_table_region_per_sheet(sample_xls: Path) -> None:
    # sample_xls (conftest.py) has two sheets: "Data" (has content), "Notes" (empty).
    result = XlsEngine().extract(sample_xls)

    assert result.error is None
    assert result.engine == "xlrd"
    assert [r.category for r in result.regions] == ["table"]
    assert [r.page for r in result.regions] == [1]
    assert [r.order for r in result.regions] == [0]


def test_xls_engine_table_content(sample_xls: Path) -> None:
    result = XlsEngine().extract(sample_xls)

    (data_table,) = result.tables
    assert "Name" in data_table
    assert "widgets" in data_table


def test_xls_engine_numeric_cells_come_back_as_float(sample_xls: Path) -> None:
    # Verified quirk (see xls.py docstring): xlrd's data model has no
    # integer type - a cell written as the int 42 reads back as 42.0,
    # unlike XlsxEngine where openpyxl preserves the int.
    result = XlsEngine().extract(sample_xls)
    (data_table,) = result.tables
    assert "42.0" in data_table


def test_xls_engine_no_bbox(sample_xls: Path) -> None:
    result = XlsEngine().extract(sample_xls)
    assert all(r.bbox is None for r in result.regions)


def test_xls_engine_skips_empty_sheets(tmp_path: Path) -> None:
    import xlwt

    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("HasData")
    sheet.write(0, 0, "content")
    workbook.add_sheet("Empty")
    path = tmp_path / "with_empty_sheet.xls"
    workbook.save(str(path))

    result = XlsEngine().extract(path)

    assert len(result.regions) == 1
    assert "content" in result.tables[0]


def test_xls_engine_rejects_non_xls_file(dense_text_pdf: Path) -> None:
    result = XlsEngine().extract(dense_text_pdf)

    assert result.error is not None
    assert "xls" in result.error
    assert "pdf" in result.error
