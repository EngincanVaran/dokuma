"""CSV/TSV inspection - stdlib `csv` module only, no dependency needed.

`.tsv` forces a tab delimiter rather than relying on sniffing (which is
fine for real CSVs but not worth trusting to correctly infer tabs on a
file already telling us via its extension).
"""

from __future__ import annotations

import csv
from pathlib import Path

from dokuma.types import DocumentInfo

_SAMPLE_CHARS = 8192


def _detect_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample).delimiter
    except csv.Error:
        return ","


class CsvInspector:
    format = "csv"

    def inspect(self, path: Path) -> DocumentInfo:
        text = path.read_text(encoding="utf-8", errors="replace")
        is_tsv = path.suffix.lower() == ".tsv"
        delimiter = "\t" if is_tsv else _detect_delimiter(text[:_SAMPLE_CHARS])

        try:
            has_header = csv.Sniffer().has_header(text[:_SAMPLE_CHARS])
        except csv.Error:
            has_header = False

        rows = list(csv.reader(text.splitlines(), delimiter=delimiter))
        column_count = len(rows[0]) if rows else 0

        return DocumentInfo(
            path=path,
            format="tsv" if is_tsv else "csv",
            size_bytes=path.stat().st_size,
            row_count=len(rows),
            column_count=column_count,
            metadata={"delimiter": repr(delimiter), "has_header": str(has_header)},
        )
