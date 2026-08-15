"""`inspect()`: fast document metadata - page count, size, format-specific
signal (e.g. a PDF's text/scanned classification) - without doing full
content extraction. Dispatches to a per-format Inspector instance by
extension.
"""

from __future__ import annotations

from pathlib import Path

from dokuma.detect import UnsupportedFormatError, detect_format
from dokuma.inspectors.base import Inspector
from dokuma.inspectors.csv import CsvInspector
from dokuma.inspectors.docx import DocxInspector
from dokuma.inspectors.email_ import EmailInspector
from dokuma.inspectors.html import HtmlInspector
from dokuma.inspectors.markdown import MarkdownInspector
from dokuma.inspectors.msg import MsgInspector
from dokuma.inspectors.pdf import PdfInspector
from dokuma.inspectors.xls import XlsInspector
from dokuma.inspectors.xlsb import XlsbInspector
from dokuma.inspectors.xlsx import XlsxInspector
from dokuma.types import DocumentInfo

_INSPECTORS: dict[str, Inspector] = {
    "pdf": PdfInspector(),
    "docx": DocxInspector(),
    "xlsx": XlsxInspector(),
    "xls": XlsInspector(),
    "xlsb": XlsbInspector(),
    "html": HtmlInspector(),
    "markdown": MarkdownInspector(),
    "csv": CsvInspector(),
    "email": EmailInspector(),
    "msg": MsgInspector(),
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
    return inspector.inspect(path)
