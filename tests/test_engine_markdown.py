from __future__ import annotations

from pathlib import Path

from dokuma.engines.markdown import MarkdownEngine


def test_markdown_engine_headings_and_text_no_table(sample_markdown: Path) -> None:
    result = MarkdownEngine().extract(sample_markdown)

    assert result.error is None
    assert result.engine == "markdown"
    categories = [r.category for r in result.regions]
    assert categories == ["heading", "text", "heading", "text", "heading", "text"]


def test_markdown_engine_interleaves_text_and_table_in_order(markdown_with_table: Path) -> None:
    result = MarkdownEngine().extract(markdown_with_table)

    categories = [r.category for r in result.regions]
    assert categories == ["heading", "text", "table", "heading", "text"]
    assert [r.order for r in result.regions] == [0, 1, 2, 3, 4]


def test_markdown_engine_table_content(markdown_with_table: Path) -> None:
    result = MarkdownEngine().extract(markdown_with_table)
    assert result.tables == [
        "<table><tr><td>Name</td><td>Value</td></tr><tr><td>widgets</td><td>42</td></tr></table>"
    ]


def test_markdown_engine_no_bbox_or_page(markdown_with_table: Path) -> None:
    result = MarkdownEngine().extract(markdown_with_table)
    assert all(r.bbox is None for r in result.regions)
    assert all(r.page is None for r in result.regions)


def test_markdown_engine_rejects_non_markdown_file(dense_text_pdf: Path) -> None:
    result = MarkdownEngine().extract(dense_text_pdf)

    assert result.error is not None
    assert "markdown" in result.error
    assert "pdf" in result.error
