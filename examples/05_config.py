"""ExtractConfig: two knobs, both deliberately minimal.

- table_format ("html" default / "markdown" / "xml") controls what
  `.tables` returns. Regions always store tables as HTML internally
  regardless - this is a read-time presentation choice.
- extract_images (True default) skips image extraction entirely when set
  False - real, avoidable per-engine cost (rendering a crop, opening a
  second workbook handle, resolving relationship parts), not just fewer
  results.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from _generate_samples import make_sample_pdf_with_image

import dokuma
from dokuma.config import ExtractConfig


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "report.pdf"
        make_sample_pdf_with_image(path)
        engine = dokuma.PdfPlumberEngine()

        html_result = dokuma.extract(path, engine=engine)
        print("default table_format:")
        print(html_result.tables[0])

        print()

        markdown_result = dokuma.extract(
            path, engine=engine, config=ExtractConfig(table_format="markdown")
        )
        print('table_format="markdown":')
        print(markdown_result.tables[0])

        print()

        with_images = dokuma.extract(path, engine=engine)
        print("extract_images=True (default):", len(with_images.images), "image(s)")

        without_images = dokuma.extract(
            path, engine=engine, config=ExtractConfig(extract_images=False)
        )
        print("extract_images=False:", len(without_images.images), "image(s)")


if __name__ == "__main__":
    main()
