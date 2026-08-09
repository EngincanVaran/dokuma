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


def test_docx_engine_extracts_image_region_in_order(docx_with_image: Path) -> None:
    # Real bug, fixed: an image-only paragraph has .text == "", so it used
    # to be silently skipped entirely (both the paragraph AND its image) -
    # found via real-document testing, confirmed empirically that zero
    # trace of the embedded picture appeared anywhere in extraction output.
    result = DocxEngine().extract(docx_with_image)

    assert result.error is None
    categories = [r.category for r in result.regions]
    assert categories == ["text", "image", "text"]

    before, image, after = result.regions
    assert "before" in before.content
    assert "after" in after.content
    assert image.content == ""
    assert image.image_bytes is not None
    assert image.image_format == "png"
    assert [r.order for r in result.regions] == [0, 1, 2]


def test_docx_engine_image_bytes_are_the_real_original_file(docx_with_image: Path) -> None:
    import io

    from PIL import Image

    result = DocxEngine().extract(docx_with_image)
    image_region = next(r for r in result.regions if r.category == "image")

    decoded = Image.open(io.BytesIO(image_region.image_bytes))
    assert decoded.format == "PNG"
    assert decoded.size == (60, 40)  # exact original dimensions, not a re-render
