from __future__ import annotations

from pathlib import Path

from dokuma.config import ExtractConfig
from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region


class _WorkingEngine(Engine):
    name = "fake-working"
    format = "csv"

    def _extract(self, path: Path, _config: ExtractConfig) -> ExtractionResult:
        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=[Region(category="text", content="hello")],
        )


class _BrokenEngine(Engine):
    name = "fake-broken"
    format = "csv"

    def _extract(self, _path: Path, _config: ExtractConfig) -> ExtractionResult:
        raise RuntimeError("simulated engine failure")


def test_extract_accepts_a_plain_string_path(tmp_path: Path) -> None:
    # Real bug, caught by hand-testing the README example: extract()'s type
    # hint said Path but never normalized a str, so calling it directly
    # (not via dokuma.extract(), which does normalize) crashed with
    # AttributeError - violating the "never raises" contract in this
    # method's own docstring.
    path = tmp_path / "doc.csv"
    path.write_text("irrelevant")

    result = _WorkingEngine().extract(str(path))

    assert result.error is None
    assert result.regions[0].content == "hello"


def test_extract_returns_regions_and_timing(tmp_path: Path) -> None:
    path = tmp_path / "doc.csv"
    path.write_text("irrelevant")

    result = _WorkingEngine().extract(path)

    assert result.error is None
    assert result.engine == "fake-working"
    assert result.regions[0].content == "hello"
    assert result.duration_ms is not None and result.duration_ms >= 0


def test_extract_isolates_errors_instead_of_raising(tmp_path: Path) -> None:
    path = tmp_path / "doc.csv"
    path.write_text("irrelevant")

    result = _BrokenEngine().extract(path)

    assert result.error == "RuntimeError: simulated engine failure"
    assert result.regions == []
    assert result.duration_ms is not None and result.duration_ms >= 0


def test_extract_rejects_wrong_format_without_raising(tmp_path: Path) -> None:
    # _WorkingEngine only claims to handle "csv" - hand it a .pdf instead.
    path = tmp_path / "doc.pdf"
    path.write_text("irrelevant")

    result = _WorkingEngine().extract(path)

    assert result.error is not None
    assert "csv" in result.error
    assert "pdf" in result.error
    assert result.format == "pdf"  # reports the *detected* format, not the engine's
    assert result.regions == []


def test_extract_unrecognized_extension_is_a_graceful_error(tmp_path: Path) -> None:
    path = tmp_path / "doc.exe"
    path.write_text("irrelevant")

    result = _WorkingEngine().extract(path)

    assert result.error is not None
    assert result.format == "unknown"


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
