from __future__ import annotations

from pathlib import Path

import dokuma


def test_inspect_markdown_reports_structure(sample_markdown: Path) -> None:
    info = dokuma.inspect(sample_markdown)

    assert info.format == "markdown"
    assert info.size_bytes == sample_markdown.stat().st_size
    assert info.heading_count == 3
    assert info.title == "Dokuma Test Doc"
    assert info.word_count is not None and info.word_count > 0
    assert info.page_count is None
