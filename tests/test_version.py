from __future__ import annotations

import dokuma


def test_version_is_a_string() -> None:
    assert isinstance(dokuma.__version__, str)
    assert dokuma.__version__
