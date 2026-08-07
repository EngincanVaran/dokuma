"""`extract()`: structured content extraction (regions: text + tables so
far), as opposed to `inspect()`'s fast metadata-only pass. Dispatches to a
default Engine per format; pass `engine=` explicitly to use a specific one
once more than one engine exists per format.
"""

from __future__ import annotations

from pathlib import Path

from dokuma.detect import UnsupportedFormatError, detect_format
from dokuma.engines.base import Engine
from dokuma.engines.docx import DocxEngine
from dokuma.engines.pdf_inspector import PdfInspectorEngine
from dokuma.types import ExtractionResult

_DEFAULT_ENGINES: dict[str, type[Engine]] = {
    "pdf": PdfInspectorEngine,
    "docx": DocxEngine,
}


def extract(path: str | Path, engine: Engine | None = None) -> ExtractionResult:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if engine is not None:
        return engine.extract(path)

    fmt = detect_format(path)
    try:
        engine_cls = _DEFAULT_ENGINES[fmt]
    except KeyError:
        raise UnsupportedFormatError(f"Extraction not yet implemented for format {fmt!r}") from None
    return engine_cls().extract(path)
