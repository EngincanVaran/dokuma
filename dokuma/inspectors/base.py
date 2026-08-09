"""Inspector: the lightweight, class-based counterpart to Engine for
`inspect()`. Deliberately NOT an ABC, unlike Engine - every format has
exactly one inspector today, with no per-inspector config and no shared
error-isolation/timing wrapper to enforce structurally (Engine needed that
machinery because `Engine.extract()` must never raise, for safe batch use;
`inspect()` raising on a single bad file is still the documented, correct
behavior for a one-off call). `Inspector` is a structural `Protocol`
purely so `inspect.py`'s dispatch table has a real type instead of `Any` -
a class satisfies it just by having a matching `format` attribute and
`inspect` method, no subclassing required.

Promote this to an ABC (format-check + timing + never-raises, mirroring
`engines/base.py`) if a real need shows up later - multiple inspectors per
format, or per-inspector config - not before.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from dokuma.types import DocumentInfo


class Inspector(Protocol):
    format: str

    def inspect(self, path: Path) -> DocumentInfo: ...
