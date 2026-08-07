"""dokuma - unified structured extraction across document types.

See README.md for the design sketch. `inspect()` (fast metadata: page
count, size, PDF text/scanned classification) is implemented; structured
extraction is not yet.
"""

from importlib.metadata import PackageNotFoundError, version

from dokuma.detect import UnsupportedFormatError, detect_format
from dokuma.inspect import inspect
from dokuma.types import DocumentInfo

try:
    __version__ = version("dokuma")
except PackageNotFoundError:
    # not installed (e.g. running straight from a source checkout without
    # `pip install -e .` / `uv sync`) - hatch-vcs has nothing to report yet.
    __version__ = "0.0.0.dev0"

__all__ = [
    "DocumentInfo",
    "UnsupportedFormatError",
    "detect_format",
    "inspect",
]
