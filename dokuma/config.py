"""`ExtractConfig` - deliberately minimal: only knobs that something in
this codebase actually consumes, not a placeholder surface built ahead of
need. See README's "Quick start" section for the current knob list.

`table_format` is consumed differently from the other two knobs, on
purpose - see `Engine.extract()`'s docstring: it's a read-time
presentation choice (regions are always built the same way; `table_format`
only changes what `.tables` converts them to afterward). `extract_images`
and `flag_needs_ocr` both change what extraction *work* happens at all
(skipping real, avoidable cost per engine - PdfPlumberEngine's crop
rendering or its second `pdf_inspector.detect_pdf()` pass, XlsxEngine's
second full workbook parse, DocxEngine's relationship-part lookups) - so
they have to reach `_extract()` itself, not just post-process the result.
"""

from __future__ import annotations

from dataclasses import dataclass

from dokuma.tables import TABLE_FORMATS


@dataclass
class ExtractConfig:
    table_format: str = "html"  # "html" | "markdown" | "xml"
    extract_images: bool = True
    flag_needs_ocr: bool = True

    def __post_init__(self) -> None:
        if self.table_format not in TABLE_FORMATS:
            raise ValueError(f"table_format={self.table_format!r} not one of {TABLE_FORMATS}")
