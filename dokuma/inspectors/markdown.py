"""Markdown inspection - pure text heuristics, no library needed."""

from __future__ import annotations

import re
from pathlib import Path

from dokuma.types import DocumentInfo

_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)", re.MULTILINE)


class MarkdownInspector:
    format = "markdown"

    def inspect(self, path: Path) -> DocumentInfo:
        text = path.read_text(encoding="utf-8", errors="replace")
        headings = _HEADING_RE.findall(text)

        return DocumentInfo(
            path=path,
            format="markdown",
            size_bytes=path.stat().st_size,
            heading_count=len(headings),
            word_count=len(text.split()),
            title=headings[0].strip() if headings else None,
        )
