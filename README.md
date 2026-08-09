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

A Python library for extracting structured content from any document type -
PDF, DOCX, XLSX, email, HTML, and more - into one unified schema, with
automatic per-region detection of what needs OCR/VLM handling versus what can
be read natively.

## Status

**`inspect()` is implemented and tested** - fast metadata (page count, size,
format-specific structure) across 8 formats, without doing full content
extraction.

**`extract()` (structured extraction: text/table/heading regions) is
implemented for all 8 formats** - PDF has two swappable engines
(pdf-inspector, pdfplumber), the rest have one each - see "Using the
extraction engines" below. The full per-region OCR/VLM-tagging vision is
not built yet - see "Design" for current vs. planned architecture.

## Supported formats

| Format | Library | Reports |
|---|---|---|
| PDF | [pdf-inspector](https://github.com/firecrawl/pdf-inspector) + [pdfplumber](https://github.com/jsvine/pdfplumber) | page count, text/scanned/mixed classification, per-page OCR/table/column flags |
| DOCX | [python-docx](https://github.com/python-openxml/python-docx) | paragraph/table/heading counts, word count, Word's cached page count* |
| XLSX | [openpyxl](https://openpyxl.readthedocs.io/) | sheet count, sheet names, per-sheet dimensions |
| XLS (legacy) | [xlrd](https://github.com/python-excel/xlrd) | same as XLSX, minus workbook metadata (see below) |
| HTML | stdlib `html.parser` | title, heading count, word count |
| Markdown | stdlib only | heading count, word count |
| CSV / TSV | stdlib `csv` | row/column count, delimiter, header detection |
| Email (`.eml`) | stdlib `email` | subject, word count, attachment count, From/To/Date |

\* Word's cached page count is only trustworthy for files actually saved by
real Microsoft Word - files from python-docx, LibreOffice, etc. carry a
stale template placeholder instead (confirmed by testing against
python-docx's own output). `dokuma` reports it as-is rather than guessing;
see `dokuma/inspectors/docx.py` for the full explanation.

**Known, deliberate gaps:**
- Legacy `.doc` (pre-2007 binary Word) - no good pure-Python reader exists;
  the honest options all need an external tool (LibreOffice) or a heavy
  dependency. Not worth a fragile implementation.
- `.xls` workbook metadata (title/author) - xlrd doesn't parse the OLE
  `SummaryInformation` stream `.xls` stores that in.
- Outlook's binary `.msg` format - needs a separate library entirely from
  `.eml`'s stdlib `email` support.

## Installation

```bash
pip install "dokuma[pdf]"              # just PDF support
pip install "dokuma[pdf,docx,xlsx]"    # pick what you need
pip install "dokuma[all]"              # everything
```

HTML, Markdown, CSV/TSV, and email need no extra - stdlib only.
`pip install "dokuma[pandas]"` adds `ExtractionResult.tables_as_dataframes()`
- kept separate from the format extras above since it's an output-conversion
nicety, not document-format support.

## Quick start

```python
import dokuma

info = dokuma.inspect("report.pdf")
print(info.summary())
```

```
report.pdf (pdf)
  size: 5,145 bytes
  pages: 12
  type: text_based (confidence 0.50)
```

```python
if info.needs_ocr():
    print(f"Pages needing OCR: {info.pages_needing_ocr}")
```

## Using the extraction engines

`extract()` goes further than `inspect()` - instead of just metadata, it
returns `Region`s (text/table pieces of the document, in order). PDF has
**two swappable engines** with genuinely different capabilities, which is
the whole reason `Engine` is a class hierarchy rather than plain functions.

```python
import dokuma

result = dokuma.extract("quarterly.pdf")  # default: PdfInspectorEngine
print("engine:", result.engine)
for region in result.regions:
    print(f"  [{region.category}] page={region.page} bbox={region.bbox}")
```

```
engine: pdf-inspector
  [text] page=None bbox=None order=0
  [table] page=None bbox=None order=1
```

pdf-inspector is fast, but its public API doesn't expose per-region layout -
`bbox`/`page` come back `None` rather than faked. Pass `engine=` explicitly
to use pdfplumber instead, which *does* give real position data:

```python
result = dokuma.extract("quarterly.pdf", engine=dokuma.PdfPlumberEngine())
for region in result.regions:
    print(f"  [{region.category}] page={region.page} bbox={region.bbox}")

print(result.tables)  # convenience: every table region's HTML content
```

```
  [text] page=1 bbox=(0.0, 0.0, 595.28, 841.89)
  [table] page=1 bbox=(28.35, 51.02, 566.93, 123.02)
['<table><tr><td>Quarter</td><td>Revenue</td></tr>...</table>']
```

**PdfPlumberEngine also extracts embedded pictures** as `category="image"`
regions, in real reading order alongside text and tables (a picture sitting
between two paragraphs comes out between them, not bundled at the end):

```python
for region in result.regions:
    if region.category == "image":
        region.save_image(f"page{region.page}_figure.png")

print(len(result.images))  # convenience: every image region's PNG bytes, in order
```

`region.image_bytes` is a *rendered* PNG crop of the picture's bbox, not the
original embedded file's exact bytes/format - see `engines/pdf_plumber.py`
for why (short version: PDFs store images under several different, fiddly
encodings, and rendering sidesteps decoding all of them). This is currently
PDF-only, via `PdfPlumberEngine` - `PdfInspectorEngine` and every non-PDF
engine still silently drop embedded pictures, same as they always have.

**Errors never raise from an engine** - a wrong-format file, a missing path,
or an internal library crash all come back as `result.error` instead, so
looping over many files never gets aborted by one bad one:

```python
result = dokuma.PdfPlumberEngine().extract("report.docx")
print(result.error)
# pdfplumber only extracts 'pdf' files, got 'docx' (report.docx)
```

(The top-level `dokuma.extract()`/`dokuma.inspect()` are the exception -
those *do* raise on a missing file or an unsupported format, which is the
right behavior for a single one-off call rather than a batch loop.)

## Configuring extraction output

`ExtractConfig` is the first config object - one real knob so far
(`table_format`), not a placeholder surface. It controls what `.tables`
returns; regions always store tables as HTML internally regardless:

```python
from dokuma.config import ExtractConfig

result = dokuma.extract(
    "quarterly.pdf",
    engine=dokuma.PdfPlumberEngine(),
    config=ExtractConfig(table_format="markdown"),
)
print(result.tables[0])
```

```
| Name | Value |
| --- | --- |
| widgets | 42 |
```

`table_format` accepts `"html"` (default), `"markdown"`, or `"xml"`. For
pandas output (needs `dokuma[pandas]`), use `.tables_as_dataframes()`
directly - a `DataFrame` isn't a string, so it doesn't fit the same knob.

Need the whole document as one string instead of separate regions?
`.to_markdown()` renders every region in order - headings at their real
level, tables always as markdown tables regardless of `table_format`:

```python
print(result.to_markdown())
```

```
Intro paragraph before the table.

| Name | Value |
| --- | --- |
| widgets | 42 |

Closing paragraph after the table.
```

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
    pdf.py, docx.py, xlsx.py, xls.py, html.py, markdown.py, csv.py, email_.py
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
  config.py                 # ExtractConfig - table_format so far
  tables.py                   # HTML <-> markdown/xml/dataframe table conversion
  extract.py                    # extract(path, engine=None, config=None) -> ExtractionResult
  engines/
    base.py                       # Engine (ABC): _extract() + format check/timing/error isolation
    pdf_inspector.py                # PdfInspectorEngine - fast, no bbox/page data
    pdf_plumber.py                    # PdfPlumberEngine - real bbox/page data, image regions
    docx.py, xlsx.py, xls.py, html.py, markdown.py, csv.py, email_.py   # one engine each, real document order verified per-engine
```

`Engine` is a full ABC - `_extract()` is wrapped by shared format-check /
timing / "never raises" machinery (see "Using the extraction engines"
above), because multiple engines can genuinely exist per format (PDF has
two) and may carry real config later (API keys, model choice, confidence
thresholds). `Inspector` (`inspectors/base.py`) is intentionally lighter: a
structural `Protocol`, not an ABC - every format has exactly one inspector
today, with no config and no shared wrapper to enforce, so a plain
one-method class is enough. Promote it to a full ABC if that ever changes,
not before.

### Planned: OCR/VLM routing (not yet implemented)

```
dokuma/
  ocr/
    route.py     # decides which regions need OCR/VLM, and which backend
  merge.py      # stitches multi-engine results back into one document, reading order preserved
```

Current extraction covers text/table/heading/image regions, but only
`PdfPlumberEngine` produces image regions today (rendered PNG crops, no
OCR/VLM analysis of what's *in* them) - `PdfInspectorEngine` and every
non-PDF engine still silently drop embedded pictures, and DOCX/XLSX image
extraction hasn't been built yet (see "Using the extraction engines"
above for what PDF image extraction actually gives you). `EmailEngine` is
deliberately scoped down for v1 - body text only, no attachment listing
or recursive extraction into attachments.

## License

Apache-2.0 (see `LICENSE`) - placeholder choice, matches Docling and most of
the ecosystem this sits alongside; trivial to change before any real release.
