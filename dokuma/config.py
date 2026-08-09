"""`ExtractConfig` - deliberately minimal: only knobs that something in
this codebase actually consumes, not a placeholder surface built ahead of
need. More options land here once engines have real config to expose -
see README's "Using the extraction engines" section for why this was
deferred until now, and "Configuring extraction output" for why
`extract_images` was the thing that finally justified a second knob.

`table_format` and `extract_images` are consumed differently, on purpose -
see `Engine.extract()`'s docstring: `table_format` is a read-time
presentation choice (regions are always built the same way; `table_format`
only changes what `.tables` converts them to afterward), while
`extract_images` changes what extraction *work* happens at all (skipping
real, avoidable cost per engine - PdfPlumberEngine's crop rendering,
XlsxEngine's second full workbook parse, DocxEngine's relationship-part
lookups) - so it has to reach `_extract()` itself, not just post-process
the result.
"""

from __future__ import annotations

from dataclasses import dataclass

from dokuma.tables import TABLE_FORMATS


@dataclass
class ExtractConfig:
    table_format: str = "html"  # "html" | "markdown" | "xml"
    extract_images: bool = True

    def __post_init__(self) -> None:
        if self.table_format not in TABLE_FORMATS:
            raise ValueError(f"table_format={self.table_format!r} not one of {TABLE_FORMATS}")
