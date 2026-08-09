"""Email (.eml) inspection - stdlib `email` module only, no dependency
needed. Only RFC 822/.eml is supported - Outlook's binary .msg format needs
a separate library (extract-msg) and isn't handled here."""

from __future__ import annotations

from email import policy
from email.parser import BytesParser
from pathlib import Path

from dokuma.types import DocumentInfo


class EmailInspector:
    format = "email"

    def inspect(self, path: Path) -> DocumentInfo:
        with path.open("rb") as f:
            message = BytesParser(policy=policy.default).parse(f)

        attachment_count = sum(1 for _ in message.iter_attachments())

        body = message.get_body(preferencelist=("plain", "html"))
        word_count = len(body.get_content().split()) if body is not None else None

        metadata = {
            k: v
            for k, v in {
                "from": str(message.get("From", "")),
                "to": str(message.get("To", "")),
                "date": str(message.get("Date", "")),
            }.items()
            if v
        }

        subject = message.get("Subject")

        return DocumentInfo(
            path=path,
            format="email",
            size_bytes=path.stat().st_size,
            word_count=word_count,
            attachment_count=attachment_count,
            title=str(subject) if subject else None,
            metadata=metadata,
        )
