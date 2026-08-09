"""Email (.eml) extraction via stdlib `email` - no dependency needed, same
choice as `inspectors/email_.py`. Only RFC 822/.eml; Outlook's binary
.msg format needs a separate library and isn't handled here.

Deliberately scoped down for v1 (see todo.txt): the body becomes a single
text region; `Subject`/`From`/`To`/attachment filenames are message
metadata, not body content, so they're never turned into a region - same
reasoning `HtmlEngine` uses to skip `<title>` rather than emit it as text.
Attachments aren't listed or recursively extracted either; both were
explicitly deferred rather than half-built.

Prefers a `text/plain` body part. Falls back to `text/html` with tags
stripped via a minimal stdlib `HTMLParser` (no BeautifulSoup, same choice
as `HtmlEngine`) when there's no plain part - plenty of real email is
HTML-only, and emitting raw markup as "text" would be wrong.

No bbox/page: email has no fixed-position geometry. `bbox`/`page` stay
`None`.
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


class EmailEngine(Engine):
    name = "email"
    format = "email"

    def _extract(self, path: Path, _config: ExtractConfig) -> ExtractionResult:
        from email import policy
        from email.parser import BytesParser

        with path.open("rb") as f:
            message = BytesParser(policy=policy.default).parse(f)

        regions: list[Region] = []
        body = message.get_body(preferencelist=("plain", "html"))
        if body is not None:
            content = body.get_content()
            if body.get_content_type() == "text/html":
                content = _html_to_text(content)
            text = content.strip()
            if text:
                regions.append(Region(category="text", content=text, order=0))

        return ExtractionResult(
            path=path,
            format=self.format,
            engine=self.name,
            regions=regions,
        )
