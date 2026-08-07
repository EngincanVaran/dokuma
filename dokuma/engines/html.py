"""HTML extraction via stdlib html.parser - deliberately no extra
dependency (no BeautifulSoup), same choice as inspectors/html.py.

No bbox/page: HTML has no fixed-position geometry without actually
rendering it in a browser layout engine, which this library doesn't do.
`bbox`/`page` stay `None` on every region.

Block-level tags (p, div, li, h1-h6) act as text-flush boundaries -
consecutive inline text between them is batched into one "text" region,
matching the "one region per contiguous chunk" pattern the other engines
use, not one region per HTML element. `<script>`/`<style>`/`<title>`
content is skipped entirely - never real document content.
"""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region

_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_BLOCK_TAGS = {"p", "div", "li"} | _HEADING_TAGS
_SKIP_TAGS = {"script", "style", "title"}


def _clean(parts: list[str]) -> str:
    return " ".join("".join(parts).split())


class _RegionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.regions: list[Region] = []
        self._order = 0
        self._text_buffer: list[str] = []
        self._in_heading = False
        self._heading_buffer: list[str] = []
        self._heading_level: int | None = None
        self._in_table = False
        self._table_rows: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] | None = None
        self._skip_depth = 0

    def flush_text(self) -> None:
        text = _clean(self._text_buffer)
        if text:
            self.regions.append(Region(category="text", content=text, order=self._order))
            self._order += 1
        self._text_buffer.clear()

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag == "table":
            self.flush_text()
            self._in_table = True
            self._table_rows = []
        elif self._in_table and tag == "tr":
            self._current_row = []
        elif self._in_table and tag in ("td", "th"):
            self._current_cell = []
        elif tag in _HEADING_TAGS:
            self.flush_text()
            self._in_heading = True
            self._heading_buffer = []
            self._heading_level = int(tag[1])
        elif tag in _BLOCK_TAGS:
            self.flush_text()

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag == "table":
            self._in_table = False
            body = "".join(
                "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in self._table_rows
            )
            self.regions.append(
                Region(category="table", content=f"<table>{body}</table>", order=self._order)
            )
            self._order += 1
        elif self._in_table and tag == "tr":
            self._table_rows.append(self._current_row)
        elif self._in_table and tag in ("td", "th"):
            self._current_row.append(_clean(self._current_cell or []))
            self._current_cell = None
        elif tag in _HEADING_TAGS:
            heading_text = _clean(self._heading_buffer)
            if heading_text:
                self.regions.append(
                    Region(
                        category="heading",
                        content=heading_text,
                        order=self._order,
                        level=self._heading_level,
                    )
                )
                self._order += 1
            self._in_heading = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if self._in_table and self._current_cell is not None:
            self._current_cell.append(data)
        elif self._in_heading:
            self._heading_buffer.append(data)
        else:
            self._text_buffer.append(data)


class HtmlEngine(Engine):
    name = "html.parser"
    format = "html"

    def _extract(self, path: Path) -> ExtractionResult:
        parser = _RegionParser()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        parser.flush_text()

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=parser.regions,
        )
