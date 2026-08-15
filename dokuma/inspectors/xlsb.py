"""XLSB (Excel Binary Workbook) inspection via pyxlsb.

XLSB is a distinct, modern (2007+) binary-encoded Excel format - not the
same as legacy `.xls` (pre-2007 BIFF8, see `inspectors/xls.py`) and not
readable by openpyxl (`inspectors/xlsx.py`) either. Structurally it's the
same ZIP/OPC container XLSX uses, just with compact binary `.bin` parts
(BIFF12 records) instead of XML - confirmed directly by reading pyxlsb's
own source (`pyxlsb.workbook.Workbook._parse()` opens the file as a
`zipfile.ZipFile` and reads `xl/workbook.bin`).

pyxlsb is the only viable pure-Python `.xlsb` reader and is read-only -
no workbook-level metadata (title/author) and no print-page concept, same
honest gaps as `XlsInspector`/`XlsxInspector` for the same underlying
reason (no OOXML core-properties part parsed here).

**Verification gap, documented rather than hidden:** no real `.xlsb`
sample file was available to build test fixtures from - pyxlsb has no
write capability, and no other pure-Python library writes `.xlsb` either
(confirmed: XlsxWriter is XLSX-only). This was implemented directly
against pyxlsb's source and manually verified only for error-handling
paths (a non-ZIP file raises `zipfile.BadZipFile`, caught by the same
`inspect()`/`Engine.extract()` machinery as every other format) - real-
content parsing correctness has not been fixture-tested. Replace with
real tests the moment a genuine `.xlsb` file is available - see
CLAUDE.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dokuma.types import DocumentInfo


def _column_letter(index: int) -> str:
    """1-indexed column number -> spreadsheet letters (1 -> A, 27 -> AA).
    Not reused from openpyxl on purpose - `xlsb` is its own extra and
    shouldn't need to pull in openpyxl just for this."""
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _dimension_str(dimension: Any) -> str:
    if dimension is None:
        return "A1:A1"
    start = f"{_column_letter(dimension.c + 1)}{dimension.r + 1}"
    end = f"{_column_letter(dimension.c + dimension.w)}{dimension.r + dimension.h}"
    return f"{start}:{end}"


class XlsbInspector:
    format = "xlsb"

    def inspect(self, path: Path) -> DocumentInfo:
        import pyxlsb

        with pyxlsb.open_workbook(str(path)) as workbook:
            sheet_names = list(workbook.sheets)
            sheet_dimensions = {}
            for name in sheet_names:
                with workbook.get_sheet(name) as sheet:
                    sheet_dimensions[name] = _dimension_str(sheet.dimension)

        return DocumentInfo(
            path=path,
            format="xlsb",
            size_bytes=path.stat().st_size,
            sheet_count=len(sheet_names),
            sheet_names=sheet_names,
            sheet_dimensions=sheet_dimensions,
        )
