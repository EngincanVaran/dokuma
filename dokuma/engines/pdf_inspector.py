"""PDF extraction via pdf-inspector's full markdown output (`process_pdf`,
not the fast `detect_pdf` used by `inspect()`). Splits pipe-table blocks
out of the markdown into separate table regions; everything else becomes
text regions, in original document order.

No real bounding boxes or page numbers: pdf-inspector's public API doesn't
expose per-region layout data, only flattened markdown. `bbox`/`page` stay
`None` on every region this engine produces; `order` reflects position
within the flattened text, not true multi-column reading order.

Confirmed by direct testing: `process_pdf` (this engine) is sensitive to
per-page text density in a way `detect_pdf` (`inspect()`) isn't as
aggressive about - a page with only a short line or two of text can get
internally flagged as needing OCR and extract to nothing, even though the
same file's text layer reads back fine via pdfplumber. Check
`inspect(path).needs_ocr()` before trusting this engine's output on
sparse/short-text documents.
"""

from __future__ import annotations

import re
from pathlib import Path

from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region

_MD_TABLE_RE = re.compile(
    r"(?:^\|.*\|[ \t]*\n)(?:^\|[ \t:|-]+\|[ \t]*\n)(?:^\|.*\|[ \t]*\n?)*",
    re.MULTILINE,
)


def _pipe_row_to_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _md_table_to_html(block: str) -> str:
    lines = [ln for ln in block.strip("\n").split("\n") if ln.strip()]
    if len(lines) < 2:
        return ""
    rows = [_pipe_row_to_cells(line) for i, line in enumerate(lines) if i != 1]
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table>{body}</table>"


def split_into_regions(markdown: str) -> list[Region]:
    """Splits pdf-inspector's markdown into ordered text/table regions.
    A free function (not a method) so it's directly unit-testable without
    needing a real PDF or the pdf-inspector library at all."""
    regions: list[Region] = []
    last_end = 0
    order = 0
    for match in _MD_TABLE_RE.finditer(markdown):
        text_chunk = markdown[last_end : match.start()].strip()
        if text_chunk:
            regions.append(Region(category="text", content=text_chunk, order=order))
            order += 1
        table_html = _md_table_to_html(match.group())
        if table_html:
            regions.append(Region(category="table", content=table_html, order=order))
            order += 1
        last_end = match.end()

    tail = markdown[last_end:].strip()
    if tail:
        regions.append(Region(category="text", content=tail, order=order))

    return regions


class PdfInspectorEngine(Engine):
    name = "pdf-inspector"
    format = "pdf"

    def _extract(self, path: Path) -> ExtractionResult:
        import pdf_inspector

        result = pdf_inspector.process_pdf(str(path))
        regions = split_into_regions(result.markdown or "")

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=regions,
        )
