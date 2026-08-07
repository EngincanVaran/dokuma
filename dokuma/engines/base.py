"""`Engine`: one library+format combination that can extract structured
content. Multiple engines can exist per format (e.g. pdf-inspector vs.
pdfplumber for PDF) - callers pick one, or `dokuma.extract()` picks a
default. This is exactly the class-hierarchy point `inspect()` doesn't
need: engines are swappable and may carry real config later (API keys,
model choice, confidence thresholds), so a shared interface enforced
structurally (an ABC) earns its keep here in a way it wouldn't for a
handful of stateless functions.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path

from dokuma.types import ExtractionResult


class Engine(ABC):
    name: str
    format: str

    @abstractmethod
    def _extract(self, path: Path) -> ExtractionResult: ...

    def extract(self, path: Path) -> ExtractionResult:
        """Wraps `_extract` with timing + error isolation - a crash on one
        document is captured as `ExtractionResult.error`, never raised, so
        one bad file never aborts a batch of many."""
        start = time.perf_counter()
        try:
            result = self._extract(path)
            result.duration_ms = (time.perf_counter() - start) * 1000
            return result
        except Exception as exc:  # deliberately broad - see docstring
            return ExtractionResult(
                path=path,
                format=self.format,
                engine=self.name,
                duration_ms=(time.perf_counter() - start) * 1000,
                error=f"{type(exc).__name__}: {exc}",
            )
