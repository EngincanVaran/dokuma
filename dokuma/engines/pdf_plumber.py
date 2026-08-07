"""PDF extraction via pdfplumber - the point of a second PDF engine.

Unlike PdfInspectorEngine, this gives *real* position data: each table
region's bbox comes from pdfplumber's own table detection
(`page.find_tables()`), and each text region carries a real page number and
a real bbox for the text slice it covers - not `None` placeholders.

True reading order within a page, not just "text then tables": tables are
sorted by vertical position, and each page's text is sliced *between* table
boundaries via `page.crop()` (text above the first table, between each pair,
after the last one), so a table sitting above some paragraph is correctly
emitted before that paragraph's text region. Verified directly before
writing this: `page.crop((0, 0, width, table.top)).extract_text()` and the
same for the region below a table's bottom correctly isolate the text on
each side, not the whole page. An earlier version of this engine emitted
"all page text, then all tables" regardless of real position - fixed.
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
                tables = sorted(page.find_tables(), key=lambda t: t.bbox[1])
                cursor = 0.0

                for table in tables:
                    x0, top, x1, bottom = table.bbox
                    if top > cursor:
                        text_slice = page.crop((0, cursor, page.width, top)).extract_text()
                        if text_slice:
                            regions.append(
                                Region(
                                    category="text",
                                    content=text_slice,
                                    bbox=(0.0, cursor, float(page.width), float(top)),
                                    page=page_num,
                                    order=order,
                                )
                            )
                            order += 1

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
                    cursor = max(cursor, bottom)

                if cursor < page.height:
                    tail_text = page.crop((0, cursor, page.width, page.height)).extract_text()
                    if tail_text:
                        regions.append(
                            Region(
                                category="text",
                                content=tail_text,
                                bbox=(0.0, cursor, float(page.width), float(page.height)),
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
