from __future__ import annotations

from pathlib import Path

import dokuma
from dokuma.engines.xlsb import XlsbEngine


def test_xlsb_engine_dispatches_and_returns_error_not_raise(tmp_path: Path) -> None:
    # No real .xlsb fixture is available (see dokuma/engines/xlsb.py's
    # docstring) - this only confirms dispatch wiring and the "never
    # raises" contract on a genuinely bad file, not real-content parsing
    # correctness.
    path = tmp_path / "fake.xlsb"
    path.write_bytes(b"not a real xlsb file")

    result = dokuma.extract(path)

    assert result.engine == "pyxlsb"
    assert result.error is not None
    assert "zip" in result.error.lower()
    assert result.regions == []


def test_xlsb_engine_rejects_non_xlsb_file(dense_text_pdf: Path) -> None:
    result = XlsbEngine().extract(dense_text_pdf)

    assert result.error is not None
    assert "xlsb" in result.error
    assert "pdf" in result.error
