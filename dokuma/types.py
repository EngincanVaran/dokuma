"""Shared dataclasses. `DocumentInfo` is the result of `dokuma.inspect()`;
`Region`/`ExtractionResult` are what `Engine.extract()` (structured
extraction) produces."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


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
    """One piece of extracted content - a paragraph, a table, eventually a
    figure/formula. `bbox`/`page`/`order` are `None` when the engine that
    produced this region can't provide real position data (e.g. an engine
    that only returns flattened text) - left absent rather than faked."""

    category: str  # "text" | "table" | "heading" (more categories as engines support them)
    content: str  # plain text, or HTML for tables
    bbox: tuple[float, float, float, float] | None = None
    page: int | None = None
    order: int | None = None


@dataclass
class ExtractionResult:
    """What `Engine.extract()` returns - one engine's attempt at pulling
    structured content out of one document."""

    path: Path
    format: str
    engine: str
    regions: list[Region] = field(default_factory=list)
    duration_ms: float | None = None
    error: str | None = None

    @property
    def text(self) -> str:
        """Convenience: all text/heading regions, in order, joined."""
        return "\n\n".join(r.content for r in self.regions if r.category in ("text", "heading"))

    @property
    def tables(self) -> list[str]:
        """Convenience: all table regions' HTML content, in order."""
        return [r.content for r in self.regions if r.category == "table"]
