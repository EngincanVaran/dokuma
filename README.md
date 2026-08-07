<p align="center">
  <img src="assets/dokuma-logo-horizontal.png" alt="dokuma" width="480">
</p>

*Turkish for "weaving" / "woven fabric".*

A Python library for extracting structured content from any document type -
PDF, DOCX, XLSX, email, HTML, and more - into one unified schema, with
automatic per-region detection of what needs OCR/VLM handling versus what can
be read natively.

**Status: concept stage.** Not implemented yet - this repo currently holds
the design sketch and repo scaffolding.

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

## Design sketch (not yet implemented)

```
dokuma/
  types.py        # Document, Region (bbox + category + content), ExtractionResult - the unified schema
  detect.py         # file-type detection (extension + magic bytes)
  regions/
    pdf.py           # per-region extraction for PDF (text/table/image regions)
    docx.py
    xlsx.py
    email.py
  ocr/
    route.py          # decides which regions need OCR/VLM, and which backend
  merge.py          # stitches per-region results back into one document, reading order preserved
```

The core pattern: one small `Adapter` interface per source library/format,
each producing a canonical `ExtractionResult` - extended here from "one
full-document extraction per library" to "one extraction per region, mixed
across libraries as needed."

## License

Apache-2.0 (see `LICENSE`) - placeholder choice, matches Docling and most of
the ecosystem this sits alongside; trivial to change before any real release.
