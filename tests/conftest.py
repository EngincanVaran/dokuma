from __future__ import annotations

from pathlib import Path

import docx
import openpyxl
import pytest
from fpdf import FPDF


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """A real, valid, text-based 3-page PDF - not a hand-rolled byte string,
    so page count / text-layer detection are exercised against genuine PDF
    structure."""
    pdf = FPDF()
    for i in range(3):
        pdf.add_page()
        pdf.set_font("Helvetica", size=14)
        pdf.cell(text=f"Page {i + 1} of the dokuma test fixture.")

    path = tmp_path / "sample.pdf"
    pdf.output(str(path))
    return path


@pytest.fixture
def sample_docx(tmp_path: Path) -> Path:
    """python-docx doesn't populate Word's cached page-count field (only
    Word itself does, on save) - so this fixture's page_count is expected
    to come back None. That's exercised explicitly in the tests, not just
    incidental."""
    document = docx.Document()
    document.core_properties.title = "Dokuma Test Document"
    document.core_properties.author = "dokuma"
    document.add_heading("Introduction", level=1)
    document.add_paragraph("This is the first paragraph of the test fixture.")
    document.add_heading("Details", level=2)
    document.add_paragraph("This is the second paragraph, with more words in it.")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "A"
    table.cell(0, 1).text = "B"

    path = tmp_path / "sample.docx"
    document.save(str(path))
    return path


@pytest.fixture
def sample_xlsx(tmp_path: Path) -> Path:
    workbook = openpyxl.Workbook()
    workbook.properties.title = "Dokuma Test Workbook"
    workbook.properties.creator = "dokuma"

    sheet1 = workbook.active
    sheet1.title = "Data"
    sheet1["A1"] = "Name"
    sheet1["B1"] = "Value"
    sheet1["A2"] = "widgets"
    sheet1["B2"] = 42

    sheet2 = workbook.create_sheet("Notes")
    sheet2["A1"] = "just a note"

    path = tmp_path / "sample.xlsx"
    workbook.save(str(path))
    return path


@pytest.fixture
def sample_html(tmp_path: Path) -> Path:
    html = """<!DOCTYPE html>
<html>
<head><title>Dokuma Test Page</title></head>
<body>
<h1>Welcome</h1>
<p>This is a paragraph with some words in it.</p>
<h2>Section Two</h2>
<p>Another paragraph here, also with a few words.</p>
</body>
</html>"""
    path = tmp_path / "sample.html"
    path.write_text(html, encoding="utf-8")
    return path


@pytest.fixture
def sample_markdown(tmp_path: Path) -> Path:
    text = """# Dokuma Test Doc

Some intro text with a handful of words.

## Section Two

More words go here, in this second section.

### Subsection

Even more text.
"""
    path = tmp_path / "sample.md"
    path.write_text(text, encoding="utf-8")
    return path
