from __future__ import annotations

from pathlib import Path

from dokuma.engines.docx import DocxEngine


def test_docx_engine_extracts_headings_text_table_in_order(sample_docx: Path) -> None:
    # sample_docx (conftest.py) is built in this exact order: heading,
    # paragraph, heading, paragraph, table.
    result = DocxEngine().extract(sample_docx)

    assert result.error is None
    assert result.engine == "python-docx"
    categories = [r.category for r in result.regions]
    assert categories == ["heading", "text", "heading", "text", "table"]
    assert [r.order for r in result.regions] == [0, 1, 2, 3, 4]


def test_docx_engine_heading_content(sample_docx: Path) -> None:
    result = DocxEngine().extract(sample_docx)
    headings = [r.content for r in result.regions if r.category == "heading"]
    assert headings == ["Introduction", "Details"]


def test_docx_engine_table_content(sample_docx: Path) -> None:
    result = DocxEngine().extract(sample_docx)
    assert result.tables == [
        "<table><tr><td>A</td><td>B</td></tr><tr><td></td><td></td></tr></table>"
    ]


def test_docx_engine_text_property_includes_headings(sample_docx: Path) -> None:
    result = DocxEngine().extract(sample_docx)
    assert "Introduction" in result.text
    assert "first paragraph" in result.text


def test_docx_engine_no_bbox_or_page(sample_docx: Path) -> None:
    # DOCX is a flow document - no reliable page/position data without
    # actually rendering it, so every region should have bbox/page as None.
    result = DocxEngine().extract(sample_docx)
    assert all(r.bbox is None for r in result.regions)
    assert all(r.page is None for r in result.regions)


def test_docx_engine_rejects_non_docx_file(dense_text_pdf: Path) -> None:
    result = DocxEngine().extract(dense_text_pdf)

    assert result.error is not None
    assert "docx" in result.error
    assert "pdf" in result.error
