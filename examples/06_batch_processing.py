"""Engine.extract() never raises - a wrong-format file, a missing path,
or an internal library crash all come back as `result.error` instead, so
looping over many files never gets aborted by one bad one. This is the
whole reason that contract exists: real batch pipelines can't have one
corrupt file take down the run.

(The top-level dokuma.extract()/dokuma.inspect() are the exception - those
*do* raise on a missing file or unsupported format, correct for a single
one-off call rather than a batch loop.)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from _generate_samples import make_sample_docx, make_sample_pdf, make_sample_xlsx

import dokuma


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        pdf_path = tmp / "report.pdf"
        make_sample_pdf(pdf_path)
        docx_path = tmp / "handbook.docx"
        make_sample_docx(docx_path)
        xlsx_path = tmp / "inventory.xlsx"
        make_sample_xlsx(xlsx_path)
        # A file whose extension claims .docx but isn't really one -
        # simulates the "one bad file in a big batch" scenario.
        broken_path = tmp / "corrupt.docx"
        broken_path.write_bytes(b"not actually a docx file")

        engine = dokuma.DocxEngine()
        paths = [docx_path, broken_path, pdf_path, xlsx_path]

        succeeded = 0
        failed = 0
        for path in paths:
            result = engine.extract(path)
            if result.error is not None:
                failed += 1
                print(f"FAILED  {path.name}: {result.error}")
            else:
                succeeded += 1
                print(f"OK      {path.name}: {len(result.regions)} region(s)")

        print()
        print(f"{succeeded} succeeded, {failed} failed - the loop never crashed")


if __name__ == "__main__":
    main()
