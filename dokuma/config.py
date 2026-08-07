"""`ExtractConfig` - the first config object. Deliberately minimal: one real
knob (`table_format`) that something in this codebase actually consumes,
not a placeholder surface built ahead of need. More options (per-format
settings, OCR/VLM routing thresholds) land here once engines have real
config to expose - see README's "Using the extraction engines" section for
why this was deferred until now.
"""

from __future__ import annotations

from dataclasses import dataclass

from dokuma.tables import TABLE_FORMATS


@dataclass
class ExtractConfig:
    table_format: str = "html"  # "html" | "markdown" | "xml"

    def __post_init__(self) -> None:
        if self.table_format not in TABLE_FORMATS:
            raise ValueError(f"table_format={self.table_format!r} not one of {TABLE_FORMATS}")
