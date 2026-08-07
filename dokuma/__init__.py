"""dokuma - unified structured extraction across document types.

Concept stage - see README.md for the design sketch. Nothing implemented yet.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("dokuma")
except PackageNotFoundError:
    # not installed (e.g. running straight from a source checkout without
    # `pip install -e .` / `uv sync`) - hatch-vcs has nothing to report yet.
    __version__ = "0.0.0.dev0"
