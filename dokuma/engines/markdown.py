"""Markdown extraction - pure text/regex, no library needed, same choice
as inspectors/markdown.py.

Reuses the same pipe-table detection approach as engines/pdf_inspector.py:
split on table blocks first, then split each remaining text chunk on
headings. Two passes, not one combined regex, because a table's internal
`|` rows would otherwise need to be excluded from heading matching too -
simpler to never let heading detection see table text at all.

No bbox/page: markdown is plain text, no fixed-position geometry.
`bbox`/`page` stay `None` on every region.
"""

from __future__ import annotations

import re
from pathlib import Path

from dokuma.config import ExtractConfig
from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*)$", re.MULTILINE)
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


class MarkdownEngine(Engine):
    name = "markdown"
    format = "markdown"

    def _extract(self, path: Path, _config: ExtractConfig) -> ExtractionResult:
        text = path.read_text(encoding="utf-8", errors="replace")
        regions: list[Region] = []
        order = 0
        last_end = 0

        for match in _MD_TABLE_RE.finditer(text):
            chunk = text[last_end : match.start()]
            order = _emit_text_and_headings(chunk, regions, order)

            html = _md_table_to_html(match.group())
            if html:
                regions.append(Region(category="table", content=html, order=order))
                order += 1
            last_end = match.end()

        order = _emit_text_and_headings(text[last_end:], regions, order)

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=regions,
        )
