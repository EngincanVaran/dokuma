from __future__ import annotations

from pathlib import Path

import dokuma
from dokuma.engines.msg import MsgEngine


def test_msg_engine_dispatches_and_returns_error_not_raise(tmp_path: Path) -> None:
    # No real .msg fixture is available (see dokuma/engines/msg.py's
    # docstring) - this only confirms dispatch wiring and the "never
    # raises" contract on a genuinely bad file, not real-content parsing
    # correctness.
    path = tmp_path / "fake.msg"
    path.write_bytes(b"not a real msg file")

    result = dokuma.extract(path)

    assert result.engine == "extract-msg"
    assert result.error is not None
    assert "OLE2" in result.error
    assert result.regions == []


def test_msg_engine_rejects_non_msg_file(dense_text_pdf: Path) -> None:
    result = MsgEngine().extract(dense_text_pdf)

    assert result.error is not None
    assert "msg" in result.error
    assert "pdf" in result.error
