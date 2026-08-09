"""PDF extraction via pdf-inspector's full markdown output (`process_pdf`,
not the fast `detect_pdf` used by `inspect()`). Splits pipe-table blocks
out of the markdown into separate table regions, then splits each
remaining chunk on markdown heading syntax (`#`.."######") into
heading/text regions - the exact same two-pass approach and
`_HEADING_RE` pattern `engines/markdown.py` uses, reused here because
pdf-inspector's own markdown output uses the same `#` syntax for
headings. (`engines/markdown.py`'s docstring already cross-references
this module for the table-splitting half of the same approach - keep
both docstrings honest if either changes.)

Real bug once shipped and fixed: this engine used to leave `#`/`##`
markdown heading syntax embedded verbatim inside `category="text"`
regions instead of parsing it into real `category="heading"` regions -
found via real-document testing, not a unit test. Confirmed inconsistent
with every other multi-format engine (DOCX/HTML/Markdown all produce real
heading regions); code filtering by `category == "heading"` silently
found nothing for PDFs via this engine. Fixed by running the same
heading-splitting pass `MarkdownEngine` already had.

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

from dokuma.config import ExtractConfig
from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region

_MD_TABLE_RE = re.compile(
    r"(?:^\|.*\|[ \t]*\n)(?:^\|[ \t:|-]+\|[ \t]*\n)(?:^\|.*\|[ \t]*\n?)*",
    re.MULTILINE,
)
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*)$", re.MULTILINE)


def _pipe_row_to_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _md_table_to_html(block: str) -> str:
    lines = [ln for ln in block.strip("\n").split("\n") if ln.strip()]
    if len(lines) < 2:
        return ""
    rows = [_pipe_row_to_cells(line) for i, line in enumerate(lines) if i != 1]
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table>{body}</table>"


def _emit_text_and_headings(chunk: str, regions: list[Region], order: int) -> int:
    last_end = 0
    for match in _HEADING_RE.finditer(chunk):
        text_part = chunk[last_end : match.start()].strip()
        if text_part:
            regions.append(Region(category="text", content=text_part, order=order))
            order += 1
        heading_text = match.group(2).strip()
        if heading_text:
            regions.append(
                Region(
                    category="heading",
                    content=heading_text,
                    order=order,
                    level=len(match.group(1)),
                )
            )
            order += 1
        last_end = match.end()

    tail = chunk[last_end:].strip()
    if tail:
        regions.append(Region(category="text", content=tail, order=order))
        order += 1
    return order


def split_into_regions(markdown: str) -> list[Region]:
    """Splits pdf-inspector's markdown into ordered text/heading/table
    regions. A free function (not a method) so it's directly unit-testable
    without needing a real PDF or the pdf-inspector library at all."""
    regions: list[Region] = []
    last_end = 0
    order = 0
    for match in _MD_TABLE_RE.finditer(markdown):
        text_chunk = markdown[last_end : match.start()]
        order = _emit_text_and_headings(text_chunk, regions, order)

        table_html = _md_table_to_html(match.group())
        if table_html:
            regions.append(Region(category="table", content=table_html, order=order))
            order += 1
        last_end = match.end()

    _emit_text_and_headings(markdown[last_end:], regions, order)

    return regions


class PdfInspectorEngine(Engine):
    name = "pdf-inspector"
    format = "pdf"

    def _extract(self, path: Path, _config: ExtractConfig) -> ExtractionResult:
        import pdf_inspector

        result = pdf_inspector.process_pdf(str(path))
        regions = split_into_regions(result.markdown or "")

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=regions,
        )
