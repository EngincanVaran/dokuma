<p align="center">
  <img src="assets/dokuma-logo-horizontal.png" alt="dokuma" width="480">
</p>

<p align="center">
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://mypy-lang.org/"><img src="https://www.mypy-lang.org/static/mypy_badge.svg" alt="Checked with mypy"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue" alt="License: Apache-2.0"></a>
  <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white" alt="pre-commit enabled"></a>
</p>

*Turkish for "weaving" / "woven fabric".*

A Python library for extracting structured content - text, tables,
headings, images - from PDF, DOCX, XLSX, email, HTML, and more, into one
unified schema. Per-region OCR/VLM routing (automatically detecting what
needs OCR vs. what can be read natively) is the long-term vision, not
built yet - see "Design" below for what's real today.

## Status

**`inspect()` is implemented and tested** - fast metadata (page count, size,
format-specific structure) across 10 formats, without doing full content
extraction.

**`extract()` (structured extraction: text/table/heading/image regions) is
implemented for all 10 formats** - PDF has two swappable engines
(pdf-inspector, pdfplumber), the rest have one each - see "Quick start"
below and [`examples/`](examples/). Per-region OCR/VLM *tagging*
(`Region.needs_ocr`) is real for PDF; actually dispatching a flagged
region to an OCR/VLM backend is still just a vision - see "Design" for
current vs. planned architecture.

**XLSB and `.msg` are unverified against real files** (see "Supported
formats" below) - no real sample file was available while building
them, so unlike every other format they're implemented directly against
library source/docs rather than fixture-tested. Error-handling is
verified; real-content parsing correctness isn't yet.

## Supported formats

| Format | Library | Reports |
|---|---|---|
| PDF | [pdf-inspector](https://github.com/firecrawl/pdf-inspector) + [pdfplumber](https://github.com/jsvine/pdfplumber) | page count, text/scanned/mixed classification, per-page OCR/table/column flags |
| DOCX | [python-docx](https://github.com/python-openxml/python-docx) | paragraph/table/heading counts, word count, Word's cached page count* |
| XLSX | [openpyxl](https://openpyxl.readthedocs.io/) | sheet count, sheet names, per-sheet dimensions |
| XLS (legacy) | [xlrd](https://github.com/python-excel/xlrd) | same as XLSX, minus workbook metadata (see below) |
| XLSB† | [pyxlsb](https://github.com/willtrnr/pyxlsb) | sheet count, sheet names, per-sheet dimensions |
| HTML | stdlib `html.parser` | title, heading count, word count |
| Markdown | stdlib only | heading count, word count |
| CSV / TSV | stdlib `csv` | row/column count, delimiter, header detection |
| Email (`.eml`) | stdlib `email` | subject, word count, attachment count, From/To/Date |
| Outlook (`.msg`)† | [extract-msg](https://github.com/TeamMsgExtractor/msg-extractor) | subject, word count, attachment count, From/To/Date |

\* Word's cached page count is only trustworthy for files actually saved by
real Microsoft Word - files from python-docx, LibreOffice, etc. carry a
stale template placeholder instead (confirmed by testing against
python-docx's own output). `dokuma` reports it as-is rather than guessing;
see `dokuma/inspectors/docx.py` for the full explanation.

† **XLSB and `.msg` are implemented but not fixture-tested against real
files** - no pure-Python library writes either format, so unlike every
other format here there was no way to generate a genuine sample file to
verify against (only manually confirmed error-handling on deliberately
bad input). Treat these two with more caution than the rest until real
test coverage exists - see `dokuma/inspectors/xlsb.py` /
`dokuma/inspectors/msg.py` for the full explanation. `.msg` also needs
`dokuma[msg]`, a much heavier install than any other extra here (see
"Installation" below).

**Known, deliberate gaps:**
- Legacy `.doc` (pre-2007 binary Word) - no good pure-Python reader exists;
  the honest options all need an external tool (LibreOffice) or a heavy
  dependency. Not worth a fragile implementation.
- `.xls`/`.xlsb` workbook metadata (title/author) - neither xlrd nor
  pyxlsb parses it.

## Installation

```bash
pip install "dokuma[pdf]"              # just PDF support
pip install "dokuma[pdf,docx,xlsx]"    # pick what you need
pip install "dokuma[all]"              # everything
```

HTML, Markdown, CSV/TSV, and email (`.eml`) need no extra - stdlib only.
`pip install "dokuma[xlsb]"` adds Excel Binary Workbook support (light -
one dependency). `pip install "dokuma[msg]"` adds Outlook `.msg` support -
**much heavier** than every other extra here (~15 transitive
dependencies, including tooling unrelated to basic parsing); a deliberate
tradeoff, not an oversight - see the XLSB/`.msg` footnote above.
`pip install "dokuma[pandas]"` adds `ExtractionResult.tables_as_dataframes()`
- kept separate from the format extras above since it's an output-conversion
nicety, not document-format support.

## Quick start

```python
import dokuma

info = dokuma.inspect("report.pdf")
print(info.summary())

result = dokuma.extract("report.pdf")
print(result.text)
print(result.tables)
```

A few things worth knowing before you dig in:

- **PDF has two swappable engines** - the default (`pdf-inspector`) is
  fast but gives no bbox/page data; pass `engine=dokuma.PdfPlumberEngine()`
  for real position data and image extraction.
- **Image extraction** works for PDF (via `PdfPlumberEngine`), DOCX, and
  XLSX - embedded pictures come back as `category="image"` regions you
  save with `region.save_image(path)`. Every other engine still drops
  images silently.
- **Engines never raise** - a wrong-format file or internal crash comes
  back as `result.error`, so looping over many files never aborts on one
  bad one. (The top-level `dokuma.extract()`/`inspect()` *do* raise, which
  is correct for a single one-off call.)
- **`ExtractConfig`** has three knobs: `table_format`
  (`"html"`/`"markdown"`/`"xml"`, controls what `.tables` returns),
  `extract_images` (skip real per-engine image-extraction cost when you
  don't need it), and `flag_needs_ocr` (PDF-only, via `PdfPlumberEngine` -
  sets `region.needs_ocr=True` on regions from pages pdf-inspector's
  classifier flagged as unreliable to read natively; fires more broadly
  than "this text is garbled" - a page with plenty of real text and an
  embedded image gets flagged too, confirmed directly).

See [`examples/`](examples/) for runnable scripts covering all of the
above in depth - engine comparison, image extraction, config options, and
batch processing with error handling.

## The idea

Real documents are rarely one content type. A single page can carry prose,
a table, and a chart image all at once. Today, using that page well means
manually picking a PDF library for the text, a different one (or a table
model) for the table, and OCR or a VLM for the image - then stitching the
results back together yourself.

`dokuma` aims to do that stitching for you:

1. **Detect regions on a page** - text, table, figure/image, formula - each
   with a bounding box and a reading-order position.
2. **Tag each region with what it needs** - a native text layer read, a
   table-structure extraction, or OCR/VLM handling because it's an image or
   scanned content.
3. **Dispatch each region to the right backend** and merge everything back
   into one document, in reading order.
4. **Support more than PDFs** - DOCX, XLSX, email, HTML - through the same
   unified output shape, so downstream code (e.g. a RAG ingestion pipeline)
   never needs to know or care what the source format was.

## Prior art (know before building)

This space is not empty - worth reading before writing code, so `dokuma`
earns a reason to exist rather than reinventing an existing tool:

- **[Docling](https://github.com/DS4SD/docling)** (IBM) - layout ML model +
  table-structure model + OCR fallback, PDF/DOCX/PPTX/HTML. The closest
  architectural cousin to this idea. Requires torch.
- **[unstructured](https://github.com/Unstructured-IO/unstructured)** - very
  broad format support, partitioning API, widely used in RAG pipelines.
- **[markitdown](https://github.com/microsoft/markitdown)** (Microsoft) -
  converts many formats to Markdown for LLM consumption.
- **[dedoc](https://github.com/ispras/dedoc)** - parses PDF/DOCX/HTML/images
  into a uniform structured format with logical-structure extraction.
- **Apache Tika** - the long-standing JVM-based "detect + extract anything"
  tool; the original inspiration for this whole category.

`dokuma`'s potential differentiators, still unproven: choosing each format's
default backend from real measured benchmarks rather than assumption;
Turkish-first quality as a first-class concern, not an afterthought; staying
light enough to run without torch where possible, since that's a real
constraint on some hardware (e.g. Intel Macs), not a hypothetical one.

## Design

### Implemented: `inspect()`

```
dokuma/
  types.py              # DocumentInfo - the shared result shape
  detect.py               # extension-based format detection
  inspect.py                # inspect(path) -> DocumentInfo, dispatches by format
  inspectors/
    base.py                  # Inspector - a structural Protocol, not an ABC (see below)
    pdf.py, docx.py, xlsx.py, xls.py, xlsb.py, html.py, markdown.py, csv.py, email_.py, msg.py
```

One small class per format (`PdfInspector`, `DocxInspector`, ...), each with
a single `inspect(path) -> DocumentInfo` method, dispatched from a single
`inspect()` entry point via a name -> instance table. Adding a format is one
more `inspectors/<name>.py` plus one dispatch-table entry - nothing else
changes.

### Implemented: structured extraction

```
dokuma/
  types.py                # Region, ExtractionResult - the shared result shape
  config.py                 # ExtractConfig - table_format, extract_images, flag_needs_ocr so far
  tables.py                   # HTML <-> markdown/xml/dataframe table conversion
  extract.py                    # extract(path, engine=None, config=None) -> ExtractionResult
  engines/
    base.py                       # Engine (ABC): _extract() + format check/timing/error isolation
    pdf_inspector.py                # PdfInspectorEngine - fast, no bbox/page data
    pdf_plumber.py                    # PdfPlumberEngine - real bbox/page data, image regions
    docx.py, xlsx.py                  # also produce image regions (original embedded bytes)
    xls.py, xlsb.py, html.py, markdown.py, csv.py, email_.py, msg.py   # one engine each
```

`Engine` is a full ABC - `_extract()` is wrapped by shared format-check /
timing / "never raises" machinery (see "Quick start" above and
[`examples/06_batch_processing.py`](examples/06_batch_processing.py)),
because multiple engines can genuinely exist per format (PDF has
two) and may carry real config later (API keys, model choice, confidence
thresholds). `Inspector` (`inspectors/base.py`) is intentionally lighter: a
structural `Protocol`, not an ABC - every format has exactly one inspector
today, with no config and no shared wrapper to enforce, so a plain
one-method class is enough. Promote it to a full ABC if that ever changes,
not before.

### Partially implemented: OCR/VLM *tagging* (routing/dispatch still planned)

```
dokuma/
  ocr/
    route.py     # decides which backend handles a flagged region, dispatches to it
  merge.py      # stitches multi-engine results back into one document, reading order preserved
```

The vision has two halves, and only the first is real: **tagging** which
regions need OCR/VLM handling (`Region.needs_ocr`, `PdfPlumberEngine`
only - see "Quick start" above), and **dispatching** flagged regions to
an actual backend and merging the result back in (not built - dokuma
hands you the flag and, for images, the raw bytes; you still pick and
call your own OCR engine or vision-LLM API). Deliberately scoped this
way: picking a backend means real cost/privacy/dependency tradeoffs
(local OCR vs. a hosted vision-LLM call) that belong to the caller, not
baked into the library.

Image regions are the other half of "what needs OCR/VLM," and are
further along: `PdfPlumberEngine`, `DocxEngine`, and `XlsxEngine`
produce image regions today (see
[`examples/04_images.py`](examples/04_images.py) for what each one
actually gives you back); `PdfInspectorEngine` and HTML/Markdown/XLS/CSV/
email still don't touch embedded pictures at all. `EmailEngine` is
deliberately scoped down for v1 - body text only, no attachment listing
or recursive extraction into attachments.

## License

Apache-2.0 (see `LICENSE`) - placeholder choice, matches Docling and most of
the ecosystem this sits alongside; trivial to change before any real release.
