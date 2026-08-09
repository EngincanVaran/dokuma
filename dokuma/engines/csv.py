"""CSV/TSV extraction via stdlib `csv` - no dependency needed, same choice
as `inspectors/csv.py`. One table region for the whole file: a CSV has no
headings or prose to split out, unlike PDF/DOCX/HTML where a table is one
kind of content among several.

`detect_format()` maps both `.csv` and `.tsv` to the same `"csv"` format
string, so this one engine handles both extensions - delimiter choice is
suffix-driven inside `_extract()`, mirroring `inspectors/csv.py`: `.tsv`
forces a tab delimiter rather than trusting `Sniffer` to infer it; `.csv`
sniffs, falling back to comma on failure.

No bbox/page: a CSV is one flat table with no sheet/page concept to
repurpose `page` for (contrast Xlsx/XlsEngine, where `page` becomes the
sheet index). `bbox`/`page` stay `None`.
"""

from __future__ import annotations

import csv
from pathlib import Path

from dokuma.config import ExtractConfig
from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region

_SAMPLE_CHARS = 8192


def _detect_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample).delimiter
    except csv.Error:
        return ","


def _rows_to_html(rows: list[list[str]]) -> str:
    rows_html = ("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return "<table>" + "".join(rows_html) + "</table>"


class CsvEngine(Engine):
    name = "csv"
    format = "csv"

    def _extract(self, path: Path, _config: ExtractConfig) -> ExtractionResult:
        text = path.read_text(encoding="utf-8", errors="replace")
        is_tsv = path.suffix.lower() == ".tsv"
        delimiter = "\t" if is_tsv else _detect_delimiter(text[:_SAMPLE_CHARS])

        rows = list(csv.reader(text.splitlines(), delimiter=delimiter))

        regions: list[Region] = []
        if rows:
            regions.append(Region(category="table", content=_rows_to_html(rows), order=0))

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=regions,
        )
