"""CSV/TSV inspection - stdlib `csv` module only, no dependency needed.

`.tsv` forces a tab delimiter rather than relying on sniffing (which is
fine for real CSVs but not worth trusting to correctly infer tabs on a
file already telling us via its extension).

`format` is always `"csv"`, even for a `.tsv` file - matches
`detect_format()`, `CsvEngine.format`, and `extract()`'s dispatch, all of
which treat `.tsv` as a delimiter variant of `"csv"`, not a separate
format. This inspector used to report `format="tsv"` here, disagreeing
with every other layer for the identical file - a real bug, found via
real-document testing, fixed by matching the rest of the codebase rather
than the other way around (see `CsvEngine`'s docstring for why `.csv`/
`.tsv` share one format bucket). Use `metadata["delimiter"]` to tell them
apart, not `format`.
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
            format="csv",
            size_bytes=path.stat().st_size,
            row_count=len(rows),
            column_count=column_count,
            metadata={"delimiter": delimiter, "has_header": str(has_header)},
        )
