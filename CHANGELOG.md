# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing has been tagged or published to PyPI yet - everything below is
still pre-release.

### Added

- `inspect(path) -> DocumentInfo`: fast metadata (page count, size,
  format-specific structure) for PDF, DOCX, XLSX, legacy XLS, HTML,
  Markdown, CSV/TSV, and email (`.eml`) - one lightweight `Inspector`
  class per format.
- `extract(path, engine=None, config=None) -> ExtractionResult`:
  structured extraction (text/table/heading/image `Region`s, in real
  document order) for all 8 of the formats above. PDF has two swappable
  engines - `PdfInspectorEngine` (default, fast, no position data) and
  `PdfPlumberEngine` (real bbox/page data); every other format has one
  engine each.
- Image region extraction: `PdfPlumberEngine` (rendered PNG crops),
  `DocxEngine` and `XlsxEngine` (original embedded file bytes) all
  produce `category="image"` regions with `region.save_image(path)` and
  `ExtractionResult.images`. Every other engine still doesn't touch
  embedded/referenced pictures.
- `ExtractConfig`: `table_format` (`"html"`/`"markdown"`/`"xml"`, controls
  what `.tables` returns) and `extract_images` (skip real per-engine
  image-extraction cost when not needed).
- `ExtractionResult.to_markdown()` and `.tables_as_dataframes()` (the
  latter needs `dokuma[pandas]`).
- `Engine.extract()` never raises - a wrong-format file, missing path, or
  internal library crash all come back as `result.error`, so batch use
  over many files never aborts on one bad one. The top-level
  `dokuma.extract()`/`dokuma.inspect()` are the exception and do raise,
  correct for a single one-off call.
- `examples/` - runnable scripts demonstrating the above.

### Fixed

Found via a real-document testing pass (realistic generated documents,
not just the unit-test fixtures), not caught by the test suite at the
time:

- CSV/TSV inspection stored the sniffed delimiter via `repr()` instead of
  the raw character, and reported `format="tsv"` for `.tsv` files even
  though extraction treats `.tsv` as a delimiter variant of `"csv"`.
- The default PDF engine never produced heading regions - `#`/`##`
  markdown syntax was left embedded in plain text regions instead of
  being parsed out.
- XLSX date-only cells rendered with a spurious `00:00:00` in table
  output (openpyxl always returns `datetime.datetime`, even for a cell
  written as `datetime.date`).
