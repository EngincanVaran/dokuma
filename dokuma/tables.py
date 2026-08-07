"""Table format conversion. Every engine already stores table regions as
simple `<table><tr><td>...</td></tr></table>` HTML (no attributes, no
nested tables) - our one canonical internal format. These functions convert
that HTML into other formats on demand, so no engine needs to know or care
what output format a caller eventually wants.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape

if TYPE_CHECKING:
    import pandas as pd

TABLE_FORMATS = ("html", "markdown", "xml")

_ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.DOTALL)
_CELL_RE = re.compile(r"<t[dh]>(.*?)</t[dh]>", re.DOTALL)


def parse_html_table(html: str) -> list[list[str]]:
    """Parses our own simple table HTML back into rows of cell strings.
    Not a general HTML-table parser - no attributes, no nested tables,
    no colspan/rowspan - only ever needs to round-trip what this
    library's own engines produce."""
    return [_CELL_RE.findall(row) for row in _ROW_RE.findall(html)]


def table_to_markdown(html: str) -> str:
    rows = parse_html_table(html)
    if not rows:
        return ""
    header, *body = rows
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join(" --- " for _ in header) + "|",
    ]
    lines += ["| " + " | ".join(row) + " |" for row in body]
    return "\n".join(lines)


def table_to_xml(html: str) -> str:
    rows = parse_html_table(html)
    lines = ["<table>"]
    for row in rows:
        lines.append("  <row>")
        lines += [f"    <cell>{escape(cell)}</cell>" for cell in row]
        lines.append("  </row>")
    lines.append("</table>")
    return "\n".join(lines)


def table_to_dataframe(html: str) -> pd.DataFrame:
    """Requires pandas - `pip install dokuma[pandas]`."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError(
            "table_to_dataframe() needs pandas - install with `pip install dokuma[pandas]`"
        ) from exc

    rows = parse_html_table(html)
    if not rows:
        return pd.DataFrame()
    header, *body = rows
    return pd.DataFrame(body, columns=header)


def convert_table(html: str, table_format: str) -> str:
    if table_format == "html":
        return html
    if table_format == "markdown":
        return table_to_markdown(html)
    if table_format == "xml":
        return table_to_xml(html)
    raise ValueError(
        f"Unknown table_format {table_format!r}, expected one of {TABLE_FORMATS} "
        "(or use table_to_dataframe()/tables_as_dataframes() for pandas output)"
    )
