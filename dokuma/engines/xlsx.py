"""XLSX extraction via openpyxl. Each sheet becomes one "table" region -
the natural structure of a spreadsheet, unlike PDF/DOCX where a table is
one kind of content among several.

`page` is repurposed as the 1-indexed sheet position, not a print page -
XLSX doesn't have print pages in any reliable sense (same reasoning
inspectors/xlsx.py uses for not reporting `page_count`). `bbox` stays
`None` - there's no meaningful pixel-position geometry for spreadsheet
cells. Empty sheets are skipped: verified directly that a sheet with no
data returns an empty `iter_rows()` in read-only mode, so "has any rows at
all" is a sufficient, cheap check.

Real bug, found via real-document testing: **openpyxl always returns
`datetime.datetime` for a date-backed cell, even one written as a plain
`datetime.date`** - confirmed directly, `sheet["A1"] = datetime.date(...)`
reads back as `datetime.datetime(..., 0, 0)`. Rendered with plain `str()`,
that's a spurious `00:00:00` on every date cell, not just genuine
midnight timestamps. Fixed with a heuristic, not a guarantee: a
`datetime.datetime` whose time component is exactly midnight renders as
date-only; a real midnight timestamp (rare in spreadsheet data, common
case is date-only cells) would render the same way and lose its time -
an accepted, documented tradeoff, not something openpyxl gives us a way
to distinguish.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region


def _cell_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime.datetime) and value.time() == datetime.time.min:
        return value.date().isoformat()
    return str(value)


def _rows_to_html(rows: list[Any]) -> str:
    rows_html = []
    for row in rows:
        cells = "".join(f"<td>{_cell_str(cell.value)}</td>" for cell in row)
        rows_html.append(f"<tr>{cells}</tr>")
    return "<table>" + "".join(rows_html) + "</table>"


class XlsxEngine(Engine):
    name = "openpyxl"
    format = "xlsx"

    def _extract(self, path: Path) -> ExtractionResult:
        import openpyxl

        workbook = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        try:
            regions: list[Region] = []
            for index, name in enumerate(workbook.sheetnames):
                sheet = workbook[name]
                rows = list(sheet.iter_rows())
                if not rows:
                    continue
                regions.append(
                    Region(
                        category="table",
                        content=_rows_to_html(rows),
                        page=index + 1,
                        order=index,
                    )
                )
        finally:
            workbook.close()

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=regions,
        )
