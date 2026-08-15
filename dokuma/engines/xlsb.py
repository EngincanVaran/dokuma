"""XLSB (Excel Binary Workbook) extraction via pyxlsb - mirrors
XlsxEngine/XlsEngine's one-table-region-per-sheet pattern. See
`inspectors/xlsb.py` for what XLSB actually is and why it needs its own
reader (distinct from both XLSX and legacy XLS).

Same `page`-as-sheet-index / `bbox=None` convention as `XlsEngine`/
`XlsxEngine` - spreadsheets have no print pages, and pyxlsb gives no
cell-level pixel geometry. Empty sheets (no rows at all) are skipped, the
same "has any rows" check the other spreadsheet engines already use.

**Verification gap, documented rather than hidden:** see
`inspectors/xlsb.py` - no real `.xlsb` sample file was available. Only
error-handling was verified manually (a non-ZIP `.xlsb` raises
`zipfile.BadZipFile`, caught by `Engine.extract()`'s broad except same as
every other engine); real-content parsing correctness is not
fixture-tested yet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dokuma.config import ExtractConfig
from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region


def _rows_to_html(rows: list[Any]) -> str:
    rows_html = []
    for row in rows:
        cells = "".join(f"<td>{cell.v if cell.v is not None else ''}</td>" for cell in row)
        rows_html.append(f"<tr>{cells}</tr>")
    return "<table>" + "".join(rows_html) + "</table>"


class XlsbEngine(Engine):
    name = "pyxlsb"
    format = "xlsb"

    def _extract(self, path: Path, _config: ExtractConfig) -> ExtractionResult:
        import pyxlsb

        regions: list[Region] = []
        with pyxlsb.open_workbook(str(path)) as workbook:
            for index, name in enumerate(workbook.sheets):
                with workbook.get_sheet(name) as sheet:
                    rows = list(sheet.rows())
                if not rows:
                    continue
                regions.append(
                    Region(
                        category="table",
                        content=_rows_to_html(rows),
                        page=index + 1,
                        order=len(regions),
                    )
                )

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=regions,
        )
