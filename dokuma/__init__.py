"""dokuma - unified structured extraction across document types.

See README.md for the design sketch. `inspect()` (fast metadata: page
count, size, format-specific structure) is implemented for PDF, DOCX,
XLSX, legacy XLS, HTML, Markdown, CSV/TSV, and email (.eml). Structured
`extract()` (text/table regions via a pluggable Engine) is implemented for
PDF (two swappable engines: pdf-inspector, pdfplumber), DOCX, XLSX, HTML,
and Markdown; more formats/engines are next.
"""

from importlib.metadata import PackageNotFoundError, version

from dokuma.detect import UnsupportedFormatError, detect_format
from dokuma.engines.base import Engine
from dokuma.engines.docx import DocxEngine
from dokuma.engines.html import HtmlEngine
from dokuma.engines.markdown import MarkdownEngine
from dokuma.engines.pdf_inspector import PdfInspectorEngine
from dokuma.engines.pdf_plumber import PdfPlumberEngine
from dokuma.engines.xlsx import XlsxEngine
from dokuma.extract import extract
from dokuma.inspect import inspect
from dokuma.types import DocumentInfo, ExtractionResult, Region

try:
    __version__ = version("dokuma")
except PackageNotFoundError:
    # not installed (e.g. running straight from a source checkout without
    # `pip install -e .` / `uv sync`) - hatch-vcs has nothing to report yet.
    __version__ = "0.0.0.dev0"

__all__ = [
    "DocumentInfo",
    "DocxEngine",
    "Engine",
    "ExtractionResult",
    "HtmlEngine",
    "MarkdownEngine",
    "PdfInspectorEngine",
    "PdfPlumberEngine",
    "Region",
    "UnsupportedFormatError",
    "XlsxEngine",
    "detect_format",
    "extract",
    "inspect",
]
