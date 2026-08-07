from __future__ import annotations

import pytest

from dokuma.tables import (
    convert_table,
    parse_html_table,
    table_to_dataframe,
    table_to_markdown,
    table_to_xml,
)

_HTML = "<table><tr><td>Name</td><td>Value</td></tr><tr><td>widgets</td><td>42</td></tr></table>"


def test_parse_html_table() -> None:
    assert parse_html_table(_HTML) == [["Name", "Value"], ["widgets", "42"]]


def test_parse_html_table_empty() -> None:
    assert parse_html_table("") == []


def test_table_to_markdown() -> None:
    assert table_to_markdown(_HTML) == ("| Name | Value |\n| --- | --- |\n| widgets | 42 |")


def test_table_to_markdown_empty() -> None:
    assert table_to_markdown("") == ""


def test_table_to_xml() -> None:
    xml = table_to_xml(_HTML)
    assert "<row>" in xml
    assert "<cell>Name</cell>" in xml
    assert "<cell>widgets</cell>" in xml


def test_table_to_xml_escapes_special_characters() -> None:
    # realistic input: our own engines never escape cell content when
    # writing <td> HTML in the first place, so a raw "&" is what
    # parse_html_table actually sees - table_to_xml must escape it once,
    # for valid XML output, not assume it's already escaped.
    html = "<table><tr><td>A & B</td></tr></table>"
    xml = table_to_xml(html)
    assert "<cell>A &amp; B</cell>" in xml


def test_table_to_dataframe() -> None:
    df = table_to_dataframe(_HTML)
    assert list(df.columns) == ["Name", "Value"]
    assert df.iloc[0]["Name"] == "widgets"
    assert df.iloc[0]["Value"] == "42"


def test_table_to_dataframe_empty() -> None:
    df = table_to_dataframe("")
    assert df.empty


def test_convert_table_html_passthrough() -> None:
    assert convert_table(_HTML, "html") == _HTML


def test_convert_table_markdown() -> None:
    assert convert_table(_HTML, "markdown") == table_to_markdown(_HTML)


def test_convert_table_xml() -> None:
    assert convert_table(_HTML, "xml") == table_to_xml(_HTML)


def test_convert_table_unknown_format_raises() -> None:
    with pytest.raises(ValueError, match="expected one of"):
        convert_table(_HTML, "yaml")
