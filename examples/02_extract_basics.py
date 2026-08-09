"""dokuma.extract(): structured extraction - text/table/heading/image
Region objects, in real document order, not just flattened text.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from _generate_samples import make_sample_docx

import dokuma


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "handbook.docx"
        make_sample_docx(path)

        result = dokuma.extract(path)

        print("engine:", result.engine)
        print()
        for region in result.regions:
            print(f"[{region.category}] {region.content[:60]!r}")

        print()
        print("--- .text (headings + paragraphs, joined) ---")
        print(result.text)

        print()
        print("--- .tables (HTML by default) ---")
        for table in result.tables:
            print(table)

        print()
        print("--- .to_markdown() (whole document as one string) ---")
        print(result.to_markdown())


if __name__ == "__main__":
    main()
