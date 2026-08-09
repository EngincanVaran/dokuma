from __future__ import annotations

from pathlib import Path

from dokuma.engines.pdf_inspector import PdfInspectorEngine, split_into_regions


def test_split_into_regions_interleaves_text_and_tables_in_order() -> None:
    markdown = "Intro paragraph.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\nClosing paragraph."

    regions = split_into_regions(markdown)

    assert [r.category for r in regions] == ["text", "table", "text"]
    assert regions[0].content == "Intro paragraph."
    assert (
        regions[1].content
        == "<table><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></table>"
    )
    assert regions[2].content == "Closing paragraph."
    assert [r.order for r in regions] == [0, 1, 2]


def test_split_into_regions_no_tables_is_one_text_region() -> None:
    regions = split_into_regions("Just plain prose, no tables here.")

    assert len(regions) == 1
    assert regions[0].category == "text"


def test_split_into_regions_empty_markdown_gives_no_regions() -> None:
    assert split_into_regions("") == []
    assert split_into_regions("   \n\n  ") == []


def test_split_into_regions_extracts_real_heading_regions() -> None:
    # Real bug, fixed: this used to leave "#"/"##" markdown syntax
    # embedded verbatim inside a single text region instead of parsing it
    # into real category="heading" regions - inconsistent with every
    # other multi-format engine, found via real-document testing.
    markdown = "# Report Title\n\nIntro paragraph.\n\n## Section One\n\nMore text."

    regions = split_into_regions(markdown)

    assert [r.category for r in regions] == ["heading", "text", "heading", "text"]
    assert [r.level for r in regions] == [1, None, 2, None]
    assert regions[0].content == "Report Title"
    assert regions[1].content == "Intro paragraph."
    assert regions[2].content == "Section One"
    assert regions[3].content == "More text."
    assert "#" not in regions[0].content
    assert [r.order for r in regions] == [0, 1, 2, 3]


def test_split_into_regions_headings_interleave_with_tables() -> None:
    markdown = "# Title\n\nIntro.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n## Section\n\nClosing."

    regions = split_into_regions(markdown)

    assert [r.category for r in regions] == ["heading", "text", "table", "heading", "text"]


def test_pdf_inspector_engine_extracts_real_text(dense_text_pdf: Path) -> None:
    # dense_text_pdf has no table (see conftest.py) - table-splitting itself
    # is covered by the pure split_into_regions tests above. This exercises
    # the real pdf-inspector call end to end.
    result = PdfInspectorEngine().extract(dense_text_pdf)

    assert result.error is None
    assert result.engine == "pdf-inspector"
    assert result.format == "pdf"
    assert "real paragraph of test content" in result.text
    assert result.duration_ms is not None and result.duration_ms > 0


def test_pdf_inspector_engine_on_sparse_pages_extracts_nothing(sample_pdf: Path) -> None:
    # Documents real, confirmed behavior, not a bug: pdf-inspector's
    # process_pdf() is sensitive to per-page text density. sample_pdf's one
    # short line per page gets flagged internally as needing OCR and
    # extracts to empty markdown, even though pdfplumber (and pdf-inspector's
    # own detect_pdf, used by inspect()) reads the same file's text layer
    # just fine. This is exactly why `inspect().needs_ocr()` exists as a
    # signal to check before trusting an extraction - not a contradiction.
    result = PdfInspectorEngine().extract(sample_pdf)

    assert result.error is None  # doesn't crash - just extracts nothing useful
    assert result.regions == []
    assert result.text == ""


def test_pdf_inspector_engine_rejects_non_pdf_file(sample_docx: Path) -> None:
    result = PdfInspectorEngine().extract(sample_docx)

    assert result.error is not None
    assert "pdf" in result.error
    assert "docx" in result.error
    assert result.regions == []
