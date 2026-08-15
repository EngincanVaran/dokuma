"""Outlook `.msg` (binary OLE-based email) inspection via extract-msg -
the only mature pure-Python `.msg` reader. Needs `dokuma[msg]`, a much
heavier extra than any other in this project (extract-msg pulls in ~15
transitive dependencies - oletools/msoffcrypto-tool for security-adjacent
parsing, even a Tkinter GUI library it doesn't need for headless use) - a
deliberate, documented tradeoff confirmed via `uv pip install --dry-run`
before accepting it, not an oversight. No lighter pure-Python `.msg`
reader exists.

**Verification gap, documented rather than hidden:** no real `.msg`
sample file was available to build test fixtures from - there is no
pure-Python `.msg` *writer* to construct one, and no Outlook/Exchange
access to export a real one from. Implemented directly against
extract-msg's source; only error-handling was verified manually (garbage
bytes with a `.msg` extension raise `extract_msg.exceptions.
InvalidFileFormatError`, confirmed directly, caught by the same
`inspect()`/`Engine.extract()` machinery as every other format) - real-
content parsing correctness is not fixture-tested yet. Replace with real
tests the moment a genuine `.msg` file is available - see CLAUDE.md.
"""

from __future__ import annotations

from pathlib import Path

from dokuma.types import DocumentInfo


class MsgInspector:
    format = "msg"

    def inspect(self, path: Path) -> DocumentInfo:
        import extract_msg

        with extract_msg.openMsg(str(path)) as msg_file:
            # openMsg() returns the base MSGFile type - a .msg can also be a
            # Contact/Appointment/etc, which don't have body/sender/subject.
            # Narrow explicitly rather than assume: a real, not hypothetical,
            # case this format's binary structure allows.
            if not isinstance(msg_file, extract_msg.Message):
                raise TypeError(
                    f"{path.name} is a .msg file but not an email message "
                    f"(got {type(msg_file).__name__})"
                )
            msg = msg_file

            body = msg.body
            word_count = len(body.split()) if body else None
            attachment_count = len(msg.attachments)

            metadata = {
                k: v
                for k, v in {
                    "from": msg.sender or "",
                    "to": msg.to or "",
                    "date": str(msg.date) if msg.date else "",
                }.items()
                if v
            }

            return DocumentInfo(
                path=path,
                format="msg",
                size_bytes=path.stat().st_size,
                word_count=word_count,
                attachment_count=attachment_count,
                title=msg.subject,
                metadata=metadata,
            )
