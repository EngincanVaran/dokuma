"""Legacy .xls (pre-2007 binary Excel) inspection via xlrd.

xlrd deliberately dropped .xlsx support at 2.0 (openpyxl handles that now) -
this is the dedicated legacy-format path, a separate library from
inspectors/xlsx.py on purpose, not a shared one.

Workbook-level metadata (title/author) isn't exposed here the way openpyxl
exposes OOXML core properties: .xls stores that in an OLE
SummaryInformation stream that xlrd doesn't parse. `title`/`metadata` stay
empty - a real gap, not an oversight.
"""

from __future__ import annotations

from pathlib import Path

from dokuma.types import DocumentInfo


def inspect_xls(path: Path) -> DocumentInfo:
    import xlrd
    from openpyxl.utils import get_column_letter

    book = xlrd.open_workbook(str(path))
    sheet_names = book.sheet_names()

    sheet_dimensions = {}
    for name in sheet_names:
        sheet = book.sheet_by_name(name)
        if sheet.ncols and sheet.nrows:
            sheet_dimensions[name] = f"A1:{get_column_letter(sheet.ncols)}{sheet.nrows}"
        else:
            sheet_dimensions[name] = "A1:A1"

    return DocumentInfo(
        path=path,
        format="xls",
        size_bytes=path.stat().st_size,
        sheet_count=book.nsheets,
        sheet_names=sheet_names,
        sheet_dimensions=sheet_dimensions,
    )
