"""PDF is the one format with two swappable extraction engines.

PdfInspectorEngine (the default) is fast but its underlying library
exposes no per-region layout, so bbox/page always come back None.
PdfPlumberEngine is slower but gives real position data - pass it via
`engine=` when you actually need bbox/page (or image regions - see
04_images.py).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from _generate_samples import make_sample_pdf

import dokuma


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "report.pdf"
        make_sample_pdf(path)

        default_result = dokuma.extract(path)
        print(f"default engine: {default_result.engine}")
        for region in default_result.regions:
            print(f"  [{region.category}] page={region.page} bbox={region.bbox}")

        print()

        plumber_result = dokuma.extract(path, engine=dokuma.PdfPlumberEngine())
        print(f"explicit engine: {plumber_result.engine}")
        for region in plumber_result.regions:
            print(f"  [{region.category}] page={region.page} bbox={region.bbox}")


if __name__ == "__main__":
    main()
