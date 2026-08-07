"""HTML inspection via the stdlib html.parser - deliberately no extra
dependency (no BeautifulSoup) for a lightweight structural summary."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from dokuma.types import DocumentInfo

_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


class _StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self.heading_count = 0
        self._in_title = False
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
        elif tag in _HEADING_TAGS:
            self.heading_count += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title = (self.title or "") + data
        self._text_parts.append(data)

    def word_count(self) -> int:
        return len(" ".join(self._text_parts).split())


def inspect_html(path: Path) -> DocumentInfo:
    parser = _StructureParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))

    return DocumentInfo(
        path=path,
        format="html",
        size_bytes=path.stat().st_size,
        heading_count=parser.heading_count,
        word_count=parser.word_count(),
        title=parser.title.strip() if parser.title else None,
    )
