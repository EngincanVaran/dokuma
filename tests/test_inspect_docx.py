from __future__ import annotations

import zipfile
from pathlib import Path

import dokuma
from dokuma.inspectors.docx import _cached_page_count


def test_inspect_docx_reports_structure(sample_docx: Path) -> None:
    info = dokuma.inspect(sample_docx)

    assert info.format == "docx"
    assert info.size_bytes == sample_docx.stat().st_size
    assert info.paragraph_count is not None and info.paragraph_count >= 4
    assert info.table_count == 1
    assert info.heading_count == 2
    assert info.word_count is not None and info.word_count > 0


def test_inspect_docx_reads_core_properties(sample_docx: Path) -> None:
    info = dokuma.inspect(sample_docx)

    assert info.title == "Dokuma Test Document"
    assert info.metadata.get("author") == "dokuma"


def test_inspect_docx_page_count_reflects_template_placeholder(sample_docx: Path) -> None:
    # python-docx's default template carries a stale, boilerplate Pages
    # value (confirmed by inspecting its own app.xml output: Pages=1
    # alongside Application="Microsoft Macintosh Word", Words=0 - none of
    # which reflect this fixture's real content). This isn't "no data",
    # it's genuinely-present-but-meaningless data - inspect_docx reports
    # exactly what's in the file, which is the honest behavior; the
    # unreliability is documented on inspect_docx itself.
    info = dokuma.inspect(sample_docx)
    assert info.page_count == 1


def test_cached_page_count_reads_real_app_xml(tmp_path: Path) -> None:
    path = tmp_path / "with_cache.docx"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "docProps/app.xml",
            '<?xml version="1.0"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/'
            'officeDocument/2006/extended-properties"><Pages>7</Pages></Properties>',
        )

    assert _cached_page_count(path) == 7


def test_cached_page_count_none_when_missing(tmp_path: Path) -> None:
    path = tmp_path / "no_app_xml.docx"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("placeholder.txt", "not a real docx")

    assert _cached_page_count(path) is None
