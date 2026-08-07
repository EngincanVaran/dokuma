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
extraction. Structured *extraction* (the per-region OCR/VLM-tagging vision
below) is not built yet - see "Design" for current vs. planned architecture.

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
    pdf.py, docx.py, xlsx.py, xls.py, html.py, markdown.py, csv.py, email_.py
```

One function per format, dispatched from a single `inspect()` entry point via
a name -> function table. Adding a format is one more `inspectors/<name>.py`
plus one dispatch-table entry - nothing else changes.

### Planned: structured extraction (not yet implemented)

```
dokuma/
  regions/
    pdf.py           # per-region extraction for PDF (text/table/image regions)
    docx.py
    xlsx.py
    email.py
  ocr/
    route.py          # decides which regions need OCR/VLM, and which backend
  merge.py          # stitches per-region results back into one document, reading order preserved
```

The planned pattern: a small `Engine` interface per source library/format -
extended from "one full-document extraction per library" to "one extraction
per region, mixed across libraries as needed," with multiple swappable
engines per format once that's real (e.g. pdf-inspector vs. pdfplumber vs.
a future OCR/VLM engine).

## License

Apache-2.0 (see `LICENSE`) - placeholder choice, matches Docling and most of
the ecosystem this sits alongside; trivial to change before any real release.
