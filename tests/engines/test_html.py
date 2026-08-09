from __future__ import annotations

from pathlib import Path

from dokuma.engines.html import HtmlEngine


def test_html_engine_headings_and_text_no_table(sample_html: Path) -> None:
    result = HtmlEngine().extract(sample_html)

    assert result.error is None
    assert result.engine == "html.parser"
    categories = [r.category for r in result.regions]
    assert categories == ["heading", "text", "heading", "text"]


def test_html_engine_interleaves_text_and_table_in_order(html_with_table: Path) -> None:
    result = HtmlEngine().extract(html_with_table)

    categories = [r.category for r in result.regions]
    assert categories == ["heading", "text", "table", "heading", "text"]
    assert [r.order for r in result.regions] == [0, 1, 2, 3, 4]


def test_html_engine_table_content(html_with_table: Path) -> None:
    result = HtmlEngine().extract(html_with_table)

    assert result.tables == [
        "<table><tr><td>Name</td><td>Value</td></tr><tr><td>widgets</td><td>42</td></tr></table>"
    ]


def test_html_engine_skips_title_tag_content(sample_html: Path) -> None:
    # <title>Dokuma Test Page</title> is page metadata, not body content -
    # must not leak into a text/heading region.
    result = HtmlEngine().extract(sample_html)
    assert "Dokuma Test Page" not in result.text


def test_html_engine_no_bbox_or_page(html_with_table: Path) -> None:
    result = HtmlEngine().extract(html_with_table)
    assert all(r.bbox is None for r in result.regions)
    assert all(r.page is None for r in result.regions)


def test_html_engine_rejects_non_html_file(dense_text_pdf: Path) -> None:
    result = HtmlEngine().extract(dense_text_pdf)

    assert result.error is not None
    assert "html" in result.error
    assert "pdf" in result.error
