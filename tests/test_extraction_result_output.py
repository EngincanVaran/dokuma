from __future__ import annotations

from pathlib import Path

from dokuma.engines.docx import DocxEngine
from dokuma.engines.html import HtmlEngine
from dokuma.engines.markdown import MarkdownEngine
from dokuma.types import ExtractionResult, Region


def test_docx_heading_levels(sample_docx: Path) -> None:
    result = DocxEngine().extract(sample_docx)
    headings = [r for r in result.regions if r.category == "heading"]
    # sample_docx: add_heading("Introduction", level=1), add_heading("Details", level=2)
    assert [h.level for h in headings] == [1, 2]


def test_html_heading_levels(html_with_table: Path) -> None:
    result = HtmlEngine().extract(html_with_table)
    headings = [r for r in result.regions if r.category == "heading"]
    assert [h.level for h in headings] == [1, 2]  # h1, h2


def test_markdown_heading_levels(markdown_with_table: Path) -> None:
    result = MarkdownEngine().extract(markdown_with_table)
    headings = [r for r in result.regions if r.category == "heading"]
    assert [h.level for h in headings] == [1, 2]  # #, ##


def test_tables_as_dataframes() -> None:
    result = ExtractionResult(
        path=Path("x"),
        format="fake",
        engine="fake",
        regions=[
            Region(
                category="table",
                content="<table><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></table>",
            )
        ],
    )
    dfs = result.tables_as_dataframes()
    assert len(dfs) == 1
    assert list(dfs[0].columns) == ["A", "B"]


def test_to_markdown_renders_headings_text_and_tables_in_order() -> None:
    result = ExtractionResult(
        path=Path("x"),
        format="fake",
        engine="fake",
        regions=[
            Region(category="heading", content="Title", level=1, order=0),
            Region(category="text", content="Some prose.", order=1),
            Region(
                category="table",
                content="<table><tr><td>A</td><td>B</td></tr></table>",
                order=2,
            ),
        ],
    )

    markdown = result.to_markdown()
    lines = markdown.split("\n\n")
    assert lines[0] == "# Title"
    assert lines[1] == "Some prose."
    assert "| A | B |" in lines[2]


def test_to_markdown_defaults_heading_level_to_one_when_unknown() -> None:
    result = ExtractionResult(
        path=Path("x"),
        format="fake",
        engine="fake",
        regions=[Region(category="heading", content="No level set", level=None)],
    )
    assert result.to_markdown() == "# No level set"


def test_to_markdown_ignores_table_format_setting() -> None:
    # to_markdown() always renders markdown tables, regardless of
    # self.table_format - it's a dedicated "give me one markdown doc" view.
    result = ExtractionResult(
        path=Path("x"),
        format="fake",
        engine="fake",
        table_format="xml",
        regions=[
            Region(category="table", content="<table><tr><td>A</td></tr></table>"),
        ],
    )
    assert "| A |" in result.to_markdown()
    assert "<row>" not in result.to_markdown()
