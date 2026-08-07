"""PDF extraction via pdfplumber - the point of a second PDF engine.

Unlike PdfInspectorEngine, this gives *real* position data: each table
region's bbox comes from pdfplumber's own table detection
(`page.find_tables()`), and each text region carries a real page number and
a page-size bbox - not `None` placeholders.

Known, deliberate overlap: a page's text region is NOT stripped of table
content - pdfplumber's `extract_text()` includes everything on the page,
tables included, so a page's text region and its table region(s) share some
text. A cheap whole-page `extract_text()` call, not a more complex
"text outside detected table areas" pass - a real tradeoff, not a bug.
"""

from __future__ import annotations

from pathlib import Path

from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region


def _table_to_html(rows: list[list[str | None]]) -> str:
    body = []
    for row in rows:
        cells = "".join(f"<td>{cell or ''}</td>" for cell in row)
        body.append(f"<tr>{cells}</tr>")
    return "<table>" + "".join(body) + "</table>"


class PdfPlumberEngine(Engine):
    name = "pdfplumber"
    format = "pdf"

    def _extract(self, path: Path) -> ExtractionResult:
        import pdfplumber

        regions: list[Region] = []
        order = 0
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    regions.append(
                        Region(
                            category="text",
                            content=text,
                            bbox=(0.0, 0.0, float(page.width), float(page.height)),
                            page=page_num,
                            order=order,
                        )
                    )
                    order += 1

                for table in page.find_tables():
                    x0, top, x1, bottom = table.bbox
                    regions.append(
                        Region(
                            category="table",
                            content=_table_to_html(table.extract()),
                            bbox=(float(x0), float(top), float(x1), float(bottom)),
                            page=page_num,
                            order=order,
                        )
                    )
                    order += 1

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=regions,
        )
