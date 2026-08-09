"""Image region extraction - PDF (via PdfPlumberEngine), DOCX, and XLSX
all produce category="image" regions today; every other engine still
silently drops embedded/referenced pictures.

`region.image_bytes` isn't the same *kind* of bytes across engines -
PdfPlumberEngine renders a fresh PNG crop of the picture's bbox; DOCX/XLSX
give you back the original embedded file's bytes as-is. Check
`region.image_format` rather than assuming PNG.

Saves each extracted picture into examples/output/ so you can actually
open them afterward.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from _generate_samples import make_sample_docx, make_sample_pdf_with_image, make_sample_xlsx

import dokuma

OUTPUT_DIR = Path(__file__).parent / "output"


def extract_images(path: Path, engine: dokuma.Engine | None = None) -> None:
    result = dokuma.extract(path, engine=engine)
    image_regions = [r for r in result.regions if r.category == "image"]
    print(f"{path.name}: {len(image_regions)} image region(s), engine={result.engine}")

    for i, region in enumerate(image_regions):
        out_path = OUTPUT_DIR / f"{path.stem}_image{i}.{region.image_format}"
        region.save_image(out_path)
        print(f"  saved {out_path.name} ({len(region.image_bytes or b'')} bytes)")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        pdf_path = tmp / "report.pdf"
        make_sample_pdf_with_image(pdf_path)
        docx_path = tmp / "handbook.docx"
        make_sample_docx(docx_path)
        xlsx_path = tmp / "inventory.xlsx"
        make_sample_xlsx(xlsx_path)

        # PdfInspectorEngine (the default) never produces image regions -
        # pass PdfPlumberEngine explicitly to get them for PDF.
        extract_images(pdf_path, engine=dokuma.PdfPlumberEngine())
        extract_images(docx_path)
        extract_images(xlsx_path)

    print()
    print(f"see {OUTPUT_DIR} for the extracted pictures")


if __name__ == "__main__":
    main()
