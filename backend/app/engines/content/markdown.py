"""Minimal deterministic Markdown -> HTML converter (subset used by drafts).

Supports fenced code blocks, headings, unordered/ordered lists, blockquotes,
horizontal rules, bold/italic/inline code, links, and paragraphs. No external
dependency — deterministic output keeps publishing reproducible.
"""
import html
import re

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def to_html(markdown: str) -> str:
    blocks: list[str] = []
    lines = markdown.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # fenced code block
        if line.strip().startswith("```"):
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # closing fence
            blocks.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
            continue

        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        heading = _HEADING.match(stripped)
        if heading:
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            blocks.append("<hr>")
            i += 1
            continue

        # blockquote
        if stripped.startswith(">"):
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append("<blockquote><p>" + "<br>".join(_inline(q) for q in quote) + "</p></blockquote>")
            continue

        # unordered list
        if re.match(r"^[-*+]\s+", stripped):
            items: list[str] = []
            while i < len(lines) and re.match(r"^[-*+]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*+]\s+", "", lines[i].strip()))
                i += 1
            blocks.append("<ul>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + "</ul>")
            continue

        # ordered list
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            blocks.append("<ol>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + "</ol>")
            continue

        # paragraph (merge consecutive non-empty lines)
        para: list[str] = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not _is_block_start(lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        blocks.append("<p>" + _inline(" ".join(para)) + "</p>")

    return "\n".join(blocks)


def _is_block_start(line: str) -> bool:
    return bool(
        _HEADING.match(line)
        or line.startswith("```")
        or line.startswith(">")
        or re.match(r"^[-*+]\s+", line)
        or re.match(r"^\d+\.\s+", line)
        or re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", line)
    )


def _inline(text: str) -> str:
    """Escape HTML first, then apply inline markdown (code is protected)."""
    escaped = html.escape(text, quote=False)
    placeholders: list[str] = []

    def _stash(match: re.Match) -> str:
        placeholders.append(f"<code>{match.group(1)}</code>")
        return f"\x00{len(placeholders) - 1}\x00"

    out = _INLINE_CODE.sub(_stash, escaped)
    out = _LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', out)
    out = _BOLD.sub(r"<strong>\1</strong>", out)
    out = _ITALIC.sub(r"<em>\1</em>", out)
    for idx, code_html in enumerate(placeholders):
        out = out.replace(f"\x00{idx}\x00", code_html)
    return out
