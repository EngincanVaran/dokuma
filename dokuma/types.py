"""Shared dataclasses. `DocumentInfo` is the result of `dokuma.inspect()`;
`Region`/`ExtractionResult` are what `Engine.extract()` (structured
extraction) produces."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class DocumentInfo:
    """Lightweight metadata about a document - what `inspect()` returns.

    Fields that don't apply to every format (e.g. `pdf_type` only makes
    sense for PDFs) are `None` rather than omitted, so callers can rely on
    a single consistent shape regardless of source format.
    """

    path: Path
    format: str
    size_bytes: int
    page_count: int | None = None

    # PDF-specific (via pdf-inspector's fast classifier) - None for other formats.
    pdf_type: str | None = None  # "text_based" | "scanned" | "image_based" | "mixed"
    confidence: float | None = None
    is_complex_layout: bool | None = None
    has_encoding_issues: bool | None = None
    pages_needing_ocr: list[int] = field(default_factory=list)
    pages_with_tables: list[int] = field(default_factory=list)
    pages_with_columns: list[int] = field(default_factory=list)

    # DOCX-specific.
    paragraph_count: int | None = None
    table_count: int | None = None

    # XLSX-specific.
    sheet_count: int | None = None
    sheet_names: list[str] = field(default_factory=list)
    sheet_dimensions: dict[str, str] = field(default_factory=dict)

    # HTML/Markdown/DOCX - reusable across text-flow formats.
    heading_count: int | None = None
    word_count: int | None = None

    # CSV/TSV-specific.
    row_count: int | None = None
    column_count: int | None = None

    # Email-specific.
    attachment_count: int | None = None

    title: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    inspection_time_ms: float | None = None

    def needs_ocr(self) -> bool:
        """True if any page was flagged as needing OCR to read reliably."""
        return len(self.pages_needing_ocr) > 0

    def summary(self) -> str:
        """A short human-readable report - the "show me page count, size
        etc." view this whole type exists for."""
        lines = [
            f"{self.path.name} ({self.format})",
            f"  size: {self.size_bytes:,} bytes",
        ]
        if self.page_count is not None:
            lines.append(f"  pages: {self.page_count}")
        if self.pdf_type is not None:
            lines.append(f"  type: {self.pdf_type} (confidence {self.confidence:.2f})")
        if self.needs_ocr():
            lines.append(f"  needs OCR: pages {self.pages_needing_ocr}")
        if self.paragraph_count is not None:
            lines.append(f"  paragraphs: {self.paragraph_count}, tables: {self.table_count}")
        if self.sheet_count is not None:
            lines.append(f"  sheets: {self.sheet_count} ({', '.join(self.sheet_names)})")
        if self.heading_count is not None:
            lines.append(f"  headings: {self.heading_count}, words: {self.word_count}")
        if self.row_count is not None:
            lines.append(f"  rows: {self.row_count}, columns: {self.column_count}")
        if self.attachment_count is not None:
            lines.append(f"  attachments: {self.attachment_count}")
        if self.title:
            lines.append(f"  title: {self.title}")
        return "\n".join(lines)


@dataclass
class Region:
    """One piece of extracted content - a paragraph, a table, a figure.
    `bbox`/`page`/`order` are `None` when the engine that produced this
    region can't provide real position data (e.g. an engine that only
    returns flattened text) - left absent rather than faked. `level` (1-6)
    is set for `category="heading"` regions when the source format
    actually carries a heading level (DOCX style, HTML h1-h6, Markdown
    #-count) - `None` otherwise, never guessed.

    `image_bytes`/`image_format` are set only for `category="image"`
    regions - the picture's raw bytes and a lowercase format hint (e.g.
    `"png"`, `"jpeg"`). Not every engine gives you back the same *kind* of
    bytes: some (PdfPlumberEngine) render a fresh crop, always PNG; others
    (DocxEngine, XlsxEngine) return the original embedded file's bytes
    as-is, whatever format that happened to be - check the producing
    engine's docstring, and don't assume PNG. `content` stays `""` for
    image regions; there's no text to put there."""

    category: str  # "text" | "table" | "heading" | "image" (more as engines gain support)
    content: str  # plain text, or HTML for tables; "" for images
    bbox: tuple[float, float, float, float] | None = None
    page: int | None = None
    order: int | None = None
    level: int | None = None
    image_bytes: bytes | None = None
    image_format: str | None = None

    def save_image(self, path: str | Path) -> None:
        """Writes `image_bytes` to disk as-is (whatever `image_format`
        actually is - this does not re-encode). Only valid for
        `category="image"` regions that have `image_bytes` set - raises
        `ValueError` otherwise, since there's nothing to write."""
        if self.image_bytes is None:
            raise ValueError(
                "save_image() requires image_bytes to be set (category='image' regions only)"
            )
        Path(path).write_bytes(self.image_bytes)


@dataclass
class ExtractionResult:
    """What `Engine.extract()` returns - one engine's attempt at pulling
    structured content out of one document.

    `table_format` controls what `.tables` returns ("html" | "markdown" |
    "xml") - set via `ExtractConfig.table_format` passed to `extract()`,
    not meant to be set directly. Regions always store table content as
    HTML internally regardless of this setting - it's a presentation
    conversion applied on read, not a different extraction.
    """

    path: Path
    format: str
    engine: str
    regions: list[Region] = field(default_factory=list)
    duration_ms: float | None = None
    error: str | None = None
    table_format: str = "html"

    @property
    def text(self) -> str:
        """Convenience: all text/heading regions, in order, joined."""
        return "\n\n".join(r.content for r in self.regions if r.category in ("text", "heading"))

    @property
    def tables(self) -> list[str]:
        """Convenience: all table regions, in order, converted to
        `self.table_format` (html/markdown/xml - set via `ExtractConfig`)."""
        from dokuma.tables import convert_table

        html_tables = (r.content for r in self.regions if r.category == "table")
        return [convert_table(html, self.table_format) for html in html_tables]

    @property
    def images(self) -> list[bytes]:
        """Convenience: every image region's PNG bytes, in order. Use
        `region.save_image(path)` on an individual `Region` instead if you
        want the region's other data (bbox, page) alongside its bytes."""
        return [r.image_bytes for r in self.regions if r.image_bytes is not None]

    def tables_as_dataframes(self) -> list[pd.DataFrame]:
        """Every table region as a `pandas.DataFrame`. Ignores
        `table_format` - always converts from the underlying HTML, since a
        DataFrame isn't a string and doesn't fit the same knob. Requires
        `pip install dokuma[pandas]`."""
        from dokuma.tables import table_to_dataframe

        return [table_to_dataframe(r.content) for r in self.regions if r.category == "table"]

    def to_markdown(self) -> str:
        """Renders the whole document - every region, in order - as one
        markdown string. Tables always render as markdown tables here
        regardless of `table_format` (this method's whole point is a single
        markdown view, independent of the per-region-format config). Image
        regions render as a `[image]` placeholder, not real markdown image
        syntax - there's no file on disk to point a `![]()` at until the
        caller calls `region.save_image()` themselves."""
        from dokuma.tables import table_to_markdown

        parts: list[str] = []
        for region in self.regions:
            if region.category == "heading":
                level = region.level or 1
                parts.append(f"{'#' * level} {region.content}")
            elif region.category == "table":
                parts.append(table_to_markdown(region.content))
            elif region.category == "image":
                parts.append("[image]")
            else:
                parts.append(region.content)
        return "\n\n".join(parts)
