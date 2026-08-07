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
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region


def _rows_to_html(rows: list[Any]) -> str:
    rows_html = []
    for row in rows:
        cells = "".join(f"<td>{cell.value if cell.value is not None else ''}</td>" for cell in row)
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
