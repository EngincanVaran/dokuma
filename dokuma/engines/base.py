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

from dokuma.detect import UnsupportedFormatError, detect_format
from dokuma.types import ExtractionResult


class Engine(ABC):
    name: str
    format: str

    @abstractmethod
    def _extract(self, path: Path) -> ExtractionResult: ...

    def extract(self, path: str | Path) -> ExtractionResult:
        """Wraps `_extract` with format validation + timing + error
        isolation. Never raises - a wrong-format file for this engine, a
        bad path, or an internal crash are all captured as
        `ExtractionResult.error` instead, so one bad file never aborts a
        batch of many. (Contrast with the top-level `dokuma.extract()`,
        which *does* raise on a missing file or an unsupported format -
        reasonable for a single one-off call; not what you want when
        looping over hundreds of files with one engine.)
        """
        start = time.perf_counter()
        path = Path(path)

        try:
            detected_format = detect_format(path)
        except UnsupportedFormatError as exc:
            return ExtractionResult(
                path=path,
                format="unknown",
                engine=self.name,
                duration_ms=(time.perf_counter() - start) * 1000,
                error=str(exc),
            )

        if detected_format != self.format:
            return ExtractionResult(
                path=path,
                format=detected_format,
                engine=self.name,
                duration_ms=(time.perf_counter() - start) * 1000,
                error=(
                    f"{self.name} only extracts {self.format!r} files, "
                    f"got {detected_format!r} ({path.name})"
                ),
            )

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
