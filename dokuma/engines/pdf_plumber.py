"""PDF extraction via pdfplumber - the point of a second PDF engine.

Unlike PdfInspectorEngine, this gives *real* position data: each table
region's bbox comes from pdfplumber's own table detection
(`page.find_tables()`), and each text region carries a real page number and
a real bbox for the text slice it covers - not `None` placeholders. Image
regions (`page.images`) get the same treatment.

True reading order within a page, not just "text then tables then images":
tables and images are merged into one list of "blocks", sorted by vertical
position, and each page's text is sliced *between* block boundaries via
`page.crop()` (text above the first block, between each pair, after the
last one), so a table or picture sitting above some paragraph is correctly
emitted before that paragraph's text region. Verified directly before
writing this: `page.crop((0, 0, width, block.top)).extract_text()` and the
same for the region below a block's bottom correctly isolate the text on
each side, not the whole page. An earlier version of this engine emitted
"all page text, then all tables" regardless of real position - fixed, and
images were folded into the same fix rather than bolted on separately.

Image regions carry a *rendered* PNG crop of the image's bbox
(`page.crop(bbox).to_image(resolution=...).original`), not the original
embedded file's raw bytes. Deliberate: PDF images can be stored under any
of several filters (FlateDecode raw bitmaps, DCTDecode/JPEG, CCITT fax,
indexed palettes, ...) and decoding all of them correctly from pdfminer's
low-level stream primitives is real work with a lot of edge cases; a
rendered crop sidesteps that entirely and needs no new dependency -
`pypdfium2` (pdfplumber's rendering backend) is already a hard dependency
of pdfplumber, confirmed via `importlib.metadata.requires`. The tradeoff:
output is always a fresh PNG raster at `_IMAGE_RESOLUTION`, never the
original format/compression - acceptable for "let the caller see the
picture", not intended as bit-exact original-file recovery.

`ExtractConfig(extract_images=False)` skips `page.images` entirely, not
just the resulting regions - real savings, since rendering each crop is
the expensive part of this engine's image support, not free bookkeeping.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from dokuma.config import ExtractConfig
from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region

_IMAGE_RESOLUTION = 150


def _table_to_html(rows: list[list[str | None]]) -> str:
    body = []
    for row in rows:
        cells = "".join(f"<td>{cell or ''}</td>" for cell in row)
        body.append(f"<tr>{cells}</tr>")
    return "<table>" + "".join(body) + "</table>"


def _render_image(page: Any, bbox: tuple[float, float, float, float]) -> bytes:
    pil_image = page.crop(bbox).to_image(resolution=_IMAGE_RESOLUTION).original
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return buffer.getvalue()


class PdfPlumberEngine(Engine):
    name = "pdfplumber"
    format = "pdf"

    def _extract(self, path: Path, config: ExtractConfig) -> ExtractionResult:
        import pdfplumber

        regions: list[Region] = []
        order = 0
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                blocks: list[tuple[str, tuple[float, float, float, float], Any]] = [
                    ("table", t.bbox, t) for t in page.find_tables()
                ]
                if config.extract_images:
                    blocks += [
                        ("image", (img["x0"], img["top"], img["x1"], img["bottom"]), img)
                        for img in page.images
                    ]
                blocks.sort(key=lambda b: b[1][1])  # by top

                cursor = 0.0
                for kind, bbox, obj in blocks:
                    x0, top, x1, bottom = bbox
                    if top > cursor:
                        text_slice = page.crop((0, cursor, page.width, top)).extract_text()
                        if text_slice:
                            regions.append(
                                Region(
                                    category="text",
                                    content=text_slice,
                                    bbox=(0.0, cursor, float(page.width), float(top)),
                                    page=page_num,
                                    order=order,
                                )
                            )
                            order += 1

                    if kind == "table":
                        regions.append(
                            Region(
                                category="table",
                                content=_table_to_html(obj.extract()),
                                bbox=(float(x0), float(top), float(x1), float(bottom)),
                                page=page_num,
                                order=order,
                            )
                        )
                    else:
                        regions.append(
                            Region(
                                category="image",
                                content="",
                                bbox=(float(x0), float(top), float(x1), float(bottom)),
                                page=page_num,
                                order=order,
                                image_bytes=_render_image(page, (x0, top, x1, bottom)),
                                image_format="png",
                            )
                        )
                    order += 1
                    cursor = max(cursor, bottom)

                if cursor < page.height:
                    tail_text = page.crop((0, cursor, page.width, page.height)).extract_text()
                    if tail_text:
                        regions.append(
                            Region(
                                category="text",
                                content=tail_text,
                                bbox=(0.0, cursor, float(page.width), float(page.height)),
                                page=page_num,
                                order=order,
                            )
                        )
                        order += 1

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=regions,
        )
