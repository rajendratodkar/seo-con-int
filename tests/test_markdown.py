"""Markdown -> HTML engine tests (deterministic output, no network)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.engines.content.markdown import to_html  # noqa: E402


def test_headings_and_paragraph():
    out = to_html("# Title\n\nSome text here.")
    assert "<h1>Title</h1>" in out
    assert "<p>Some text here.</p>" in out


def test_inline_formatting():
    out = to_html("This is **bold**, *italic*, `code`, and a [link](https://example.com).")
    assert "<strong>bold</strong>" in out
    assert "<em>italic</em>" in out
    assert "<code>code</code>" in out
    assert '<a href="https://example.com">link</a>' in out


def test_lists():
    out = to_html("- one\n- two\n\n1. first\n2. second")
    assert "<ul><li>one</li><li>two</li></ul>" in out
    assert "<ol><li>first</li><li>second</li></ol>" in out


def test_html_is_escaped():
    out = to_html("A <script> tag must not survive.")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_code_block_keeps_content():
    out = to_html("```\nSELECT * FROM pages;\n```")
    assert "<pre><code>SELECT * FROM pages;</code></pre>" in out
