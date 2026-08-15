"""Outlook `.msg` extraction via extract-msg - mirrors `EmailEngine`'s
scoped-down v1 approach for `.eml`: body becomes one text region;
Subject/attachment filenames are message metadata, not body content, so
they're never turned into a region (same reasoning `HtmlEngine` uses to
skip `<title>`). Attachments aren't recursively extracted either - same
v1 scope-down as `EmailEngine`, for the same reason.

Prefers plain-text `.body`; falls back to `.htmlBody` (bytes) decoded and
stripped of markup via the same minimal stdlib `HTMLParser` approach
`EmailEngine` already uses for HTML-only `.eml` bodies - duplicated here
rather than imported, matching this project's existing convention of
small, independent per-engine modules (see `engines/email_.py`'s own
docstring for the same non-import reasoning between it and `HtmlEngine`).

Needs `dokuma[msg]` - see `inspectors/msg.py` for why that extra is much
heavier than any other in this project.

**Verification gap, documented rather than hidden:** no real `.msg`
sample file was available - see `inspectors/msg.py` for the same note.
Error-handling was verified manually; real-content parsing correctness
is not fixture-tested yet.
"""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from dokuma.config import ExtractConfig
from dokuma.engines.base import Engine
from dokuma.types import ExtractionResult, Region

_SKIP_TAGS = {"script", "style"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def text(self) -> str:
        return " ".join("".join(self._parts).split())


def _html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


class MsgEngine(Engine):
    name = "extract-msg"
    format = "msg"

    def _extract(self, path: Path, _config: ExtractConfig) -> ExtractionResult:
        import extract_msg

        regions: list[Region] = []
        with extract_msg.openMsg(str(path)) as msg_file:
            # openMsg() returns the base MSGFile type - a .msg can also be a
            # Contact/Appointment/etc, which don't have a body. Narrow
            # explicitly rather than assume: a real, not hypothetical, case
            # this format's binary structure allows.
            if not isinstance(msg_file, extract_msg.Message):
                raise TypeError(
                    f"{path.name} is a .msg file but not an email message "
                    f"(got {type(msg_file).__name__})"
                )
            msg = msg_file

            content = msg.body
            if not content and msg.htmlBody:
                content = _html_to_text(msg.htmlBody.decode("utf-8", errors="replace"))

            text = (content or "").strip()
            if text:
                regions.append(Region(category="text", content=text, order=0))

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=regions,
        )
