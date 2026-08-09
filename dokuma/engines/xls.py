"""XLS (legacy binary Excel) extraction via xlrd - mirrors XlsxEngine's
one-table-region-per-sheet pattern. A separate engine/library from
XlsxEngine on purpose: xlrd 2.0 dropped .xlsx support, openpyxl handles
that format now (same split `inspectors/xls.py` already makes).

`page` is repurposed as the 1-indexed sheet position, not a print page -
same reasoning as XlsxEngine, spreadsheets don't have print pages in any
reliable sense. `bbox` stays `None`. Empty sheets (`sheet.nrows == 0`) are
skipped, mirroring XlsxEngine's "has any rows at all" check.

Verified quirk: xlrd represents every numeric cell as `float` - its own
data model, not a bug - so a cell written as the int `42` reads back as
`42.0`. Reported as-is rather than reformatted, the same "don't silently
smooth over a library's real behavior" choice `inspectors/xls.py` makes
for the stale-page-count-equivalent gap (workbook metadata). This is why
`XlsEngine` and `XlsxEngine` can render the same logical number
differently - a real, documented difference between the two formats/
libraries, not an inconsistency to "fix".
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region


def _rows_to_html(rows: list[Any]) -> str:
    rows_html = []
    for row in rows:
        cells = "".join(f"<td>{cell.value}</td>" for cell in row)
        rows_html.append(f"<tr>{cells}</tr>")
    return "<table>" + "".join(rows_html) + "</table>"


class XlsEngine(Engine):
    name = "xlrd"
    format = "xls"

    def _extract(self, path: Path) -> ExtractionResult:
        import xlrd

        book = xlrd.open_workbook(str(path))
        regions: list[Region] = []
        for index, name in enumerate(book.sheet_names()):
            sheet = book.sheet_by_name(name)
            if not sheet.nrows:
                continue
            regions.append(
                Region(
                    category="table",
                    content=_rows_to_html(list(sheet.get_rows())),
                    page=index + 1,
                    order=index,
                )
            )

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=regions,
        )
