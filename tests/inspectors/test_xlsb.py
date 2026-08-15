from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile

import pytest

import dokuma


def test_inspect_xlsb_dispatches_to_xlsb_inspector(tmp_path: Path) -> None:
    # No real .xlsb fixture is available (see dokuma/inspectors/xlsb.py's
    # docstring) - this only confirms dispatch and error-path behavior,
    # not real-content parsing correctness.
    path = tmp_path / "fake.xlsb"
    path.write_bytes(b"not a real xlsb file")

    with pytest.raises(BadZipFile):
        dokuma.inspect(path)
