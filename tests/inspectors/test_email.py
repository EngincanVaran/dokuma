from __future__ import annotations

from pathlib import Path

import dokuma


def test_inspect_email_reports_subject_and_body(sample_eml: Path) -> None:
    info = dokuma.inspect(sample_eml)

    assert info.format == "email"
    assert info.title == "Dokuma Test Email"
    assert info.word_count is not None and info.word_count > 0
    assert info.page_count is None


def test_inspect_email_counts_attachments(sample_eml: Path) -> None:
    info = dokuma.inspect(sample_eml)
    assert info.attachment_count == 1


def test_inspect_email_reads_headers(sample_eml: Path) -> None:
    info = dokuma.inspect(sample_eml)
    assert info.metadata["from"] == "sender@example.com"
    assert info.metadata["to"] == "recipient@example.com"
