from __future__ import annotations

from pathlib import Path

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
