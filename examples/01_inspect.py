"""dokuma.inspect(): fast metadata only, no full content extraction.

Use this when you just need to know what you're dealing with before
deciding whether (or how) to fully extract it - page count, size,
format-specific structure like a PDF's text/scanned classification.
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

        info = dokuma.inspect(path)
        print(info.summary())
        print()
        print("needs OCR:", info.needs_ocr())
        print("pdf_type:", info.pdf_type)


if __name__ == "__main__":
    main()
