"""Unit tests for markdown chunk parsing (no DB required)."""

import pytest

from llm_archive.builders.chunks import MessageChunkBuilder


@pytest.fixture
def builder(mock_session):
    # MessageChunkBuilder only needs a session for DB ops, but _parse_markdown is pure.
    return MessageChunkBuilder(mock_session)


def test_parse_markdown_heading_paragraph_and_fence(builder):
    md = (
        "# Title\n\n"
        "This is a paragraph.\n\n"
        "```python\n"
        "print('hi')\n"
        "```\n"
    )

    chunks = list(builder._parse_markdown(md))

    assert [c.chunk_type for c in chunks] == ["heading", "paragraph", "code_fence"]

    h = chunks[0]
    assert h.heading_level == 1
    assert h.heading_text == "Title"
    assert h.text == "Title"

    p = chunks[1]
    assert p.text == "This is a paragraph."

    f = chunks[2]
    assert f.info_string == "python"
    assert "print('hi')" in f.text

    # chunk_index should be sequential
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_parse_markdown_blockquote_and_list(builder):
    md = (
        "> quoted line 1\n"
        "> quoted line 2\n\n"
        "- item a\n"
        "- item b\n"
    )

    chunks = list(builder._parse_markdown(md))
    types = [c.chunk_type for c in chunks]

    assert "blockquote" in types
    assert "list" in types

    bq = next(c for c in chunks if c.chunk_type == "blockquote")
    assert "quoted line 1" in bq.text
    assert "quoted line 2" in bq.text

    lst = next(c for c in chunks if c.chunk_type == "list")
    assert "item a" in lst.text
    assert "item b" in lst.text


def test_parse_markdown_hr(builder):
    md = "alpha\n\n---\n\nbeta\n"
    chunks = list(builder._parse_markdown(md))

    assert any(c.chunk_type == "hr" for c in chunks)

    hr = next(c for c in chunks if c.chunk_type == "hr")
    assert hr.text.strip() == "---"
