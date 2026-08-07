"""`inspect()`: fast document metadata - page count, size, format-specific
signal (e.g. a PDF's text/scanned classification) - without doing full
content extraction. Dispatches to a per-format inspector by extension.
"""

from __future__ import annotations

from pathlib import Path

from dokuma.detect import UnsupportedFormatError, detect_format
from dokuma.types import DocumentInfo


def inspect(path: str | Path) -> DocumentInfo:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    fmt = detect_format(path)
    if fmt == "pdf":
        return _inspect_pdf(path)
    raise UnsupportedFormatError(f"Inspection not yet implemented for format {fmt!r}")


def _inspect_pdf(path: Path) -> DocumentInfo:
    import pdf_inspector
    import pdfplumber

    result = pdf_inspector.detect_pdf(str(path))

    metadata: dict[str, str] = {}
    try:
        with pdfplumber.open(path) as pdf:
            metadata = {k: str(v) for k, v in (pdf.metadata or {}).items()}
    except Exception:
        pass

    return DocumentInfo(
        path=path,
        format="pdf",
        size_bytes=path.stat().st_size,
        page_count=result.page_count,
        pdf_type=result.pdf_type,
        confidence=result.confidence,
        is_complex_layout=result.is_complex_layout,
        has_encoding_issues=result.has_encoding_issues,
        pages_needing_ocr=list(result.pages_needing_ocr),
        pages_with_tables=list(result.pages_with_tables),
        pages_with_columns=list(result.pages_with_columns),
        title=result.title,
        metadata=metadata,
        inspection_time_ms=result.processing_time_ms,
    )
