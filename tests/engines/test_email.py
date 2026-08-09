from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path

from dokuma.engines.email_ import EmailEngine


def test_email_engine_body_becomes_one_text_region(sample_eml: Path) -> None:
    result = EmailEngine().extract(sample_eml)

    assert result.error is None
    assert result.engine == "email"
    assert [r.category for r in result.regions] == ["text"]
    assert "body of the test email" in result.regions[0].content


def test_email_engine_skips_subject_header(sample_eml: Path) -> None:
    # Subject is message metadata, not body content - same reasoning
    # HtmlEngine uses to skip <title> rather than emit it as a region.
    result = EmailEngine().extract(sample_eml)
    assert "Dokuma Test Email" not in result.text


def test_email_engine_no_attachment_regions(sample_eml: Path) -> None:
    # sample_eml (conftest.py) carries one attachment - scoped out of v1
    # deliberately (see email_.py docstring), so it should never surface
    # as a region.
    result = EmailEngine().extract(sample_eml)
    assert "report.pdf" not in result.text


def test_email_engine_strips_html_only_body(tmp_path: Path) -> None:
    message = EmailMessage()
    message["From"] = "sender@example.com"
    message["To"] = "recipient@example.com"
    message["Subject"] = "HTML Only"
    message.set_content("<html><body><p>Hello <b>world</b></p></body></html>", subtype="html")

    path = tmp_path / "html_only.eml"
    path.write_bytes(bytes(message))

    result = EmailEngine().extract(path)

    assert result.error is None
    assert "Hello world" in result.regions[0].content
    assert "<p>" not in result.regions[0].content


def test_email_engine_strips_script_and_style_content(tmp_path: Path) -> None:
    message = EmailMessage()
    message["From"] = "sender@example.com"
    message["To"] = "recipient@example.com"
    message["Subject"] = "HTML With Script"
    html = (
        "<html><head><style>p { color: red; }</style></head>"
        "<body><script>alert('hi')</script><p>Visible text</p></body></html>"
    )
    message.set_content(html, subtype="html")

    path = tmp_path / "html_script.eml"
    path.write_bytes(bytes(message))

    result = EmailEngine().extract(path)

    assert result.regions[0].content == "Visible text"


def test_email_engine_no_body_has_no_regions(tmp_path: Path) -> None:
    message = EmailMessage()
    message["From"] = "sender@example.com"
    message["To"] = "recipient@example.com"
    message["Subject"] = "No readable body"
    message["Content-Type"] = "application/octet-stream"
    message.set_payload(b"binary data, not text/plain or text/html")

    path = tmp_path / "no_body.eml"
    path.write_bytes(bytes(message))

    result = EmailEngine().extract(path)

    assert result.error is None
    assert result.regions == []


def test_email_engine_whitespace_only_body_has_no_regions(tmp_path: Path) -> None:
    message = EmailMessage()
    message["From"] = "sender@example.com"
    message["To"] = "recipient@example.com"
    message["Subject"] = "Blank body"
    message.set_content("   \n  \n  ")

    path = tmp_path / "blank_body.eml"
    path.write_bytes(bytes(message))

    result = EmailEngine().extract(path)

    assert result.regions == []


def test_email_engine_no_bbox_or_page(sample_eml: Path) -> None:
    result = EmailEngine().extract(sample_eml)
    assert all(r.bbox is None for r in result.regions)
    assert all(r.page is None for r in result.regions)


def test_email_engine_rejects_non_email_file(dense_text_pdf: Path) -> None:
    result = EmailEngine().extract(dense_text_pdf)

    assert result.error is not None
    assert "email" in result.error
    assert "pdf" in result.error
