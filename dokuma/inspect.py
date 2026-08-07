"""`inspect()`: fast document metadata - page count, size, format-specific
signal (e.g. a PDF's text/scanned classification) - without doing full
content extraction. Dispatches to a per-format inspector by extension.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from dokuma.detect import UnsupportedFormatError, detect_format
from dokuma.inspectors.csv import inspect_csv
from dokuma.inspectors.docx import inspect_docx
from dokuma.inspectors.email_ import inspect_email
from dokuma.inspectors.html import inspect_html
from dokuma.inspectors.markdown import inspect_markdown
from dokuma.inspectors.pdf import inspect_pdf
from dokuma.inspectors.xls import inspect_xls
from dokuma.inspectors.xlsx import inspect_xlsx
from dokuma.types import DocumentInfo

_INSPECTORS: dict[str, Callable[[Path], DocumentInfo]] = {
    "pdf": inspect_pdf,
    "docx": inspect_docx,
    "xlsx": inspect_xlsx,
    "xls": inspect_xls,
    "html": inspect_html,
    "markdown": inspect_markdown,
    "csv": inspect_csv,
    "email": inspect_email,
}


def inspect(path: str | Path) -> DocumentInfo:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    fmt = detect_format(path)
    try:
        inspector = _INSPECTORS[fmt]
    except KeyError:
        raise UnsupportedFormatError(f"Inspection not yet implemented for format {fmt!r}") from None
    return inspector(path)
