from __future__ import annotations

from pathlib import Path

import dokuma


def test_inspect_html_reports_structure(sample_html: Path) -> None:
    info = dokuma.inspect(sample_html)

    assert info.format == "html"
    assert info.size_bytes == sample_html.stat().st_size
    assert info.title == "Dokuma Test Page"
    assert info.heading_count == 2
    assert info.word_count is not None and info.word_count > 0
    assert info.page_count is None
