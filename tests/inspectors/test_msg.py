from __future__ import annotations

from pathlib import Path

import pytest
from extract_msg.exceptions import InvalidFileFormatError

import dokuma


def test_inspect_msg_dispatches_to_msg_inspector(tmp_path: Path) -> None:
    # No real .msg fixture is available (see dokuma/inspectors/msg.py's
    # docstring) - this only confirms dispatch and error-path behavior,
    # not real-content parsing correctness.
    path = tmp_path / "fake.msg"
    path.write_bytes(b"not a real msg file")

    with pytest.raises(InvalidFileFormatError):
        dokuma.inspect(path)
