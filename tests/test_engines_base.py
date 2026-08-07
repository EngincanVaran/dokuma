from __future__ import annotations

from pathlib import Path

from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region


class _WorkingEngine(Engine):
    name = "fake-working"
    format = "fake"

    def _extract(self, path: Path) -> ExtractionResult:
        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=[Region(category="text", content="hello")],
        )


class _BrokenEngine(Engine):
    name = "fake-broken"
    format = "fake"

    def _extract(self, _path: Path) -> ExtractionResult:
        raise RuntimeError("simulated engine failure")


def test_extract_returns_regions_and_timing(tmp_path: Path) -> None:
    path = tmp_path / "doc.fake"
    path.write_text("irrelevant")

    result = _WorkingEngine().extract(path)

    assert result.error is None
    assert result.engine == "fake-working"
    assert result.regions[0].content == "hello"
    assert result.duration_ms is not None and result.duration_ms >= 0


def test_extract_isolates_errors_instead_of_raising(tmp_path: Path) -> None:
    path = tmp_path / "doc.fake"
    path.write_text("irrelevant")

    result = _BrokenEngine().extract(path)

    assert result.error == "RuntimeError: simulated engine failure"
    assert result.regions == []
    assert result.duration_ms is not None and result.duration_ms >= 0


def test_extraction_result_text_and_tables_properties() -> None:
    result = ExtractionResult(
        path=Path("x"),
        format="fake",
        engine="fake",
        regions=[
            Region(category="text", content="first"),
            Region(category="table", content="<table></table>"),
            Region(category="text", content="second"),
        ],
    )

    assert result.text == "first\n\nsecond"
    assert result.tables == ["<table></table>"]
