# md_to_logseq.py
from __future__ import annotations

import re
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def md_to_logseq_outline(markdown: str, indent: str = "  ") -> str:
    """
    Convert simple longform Markdown into Logseq-style outline Markdown.

    Rules:
    - Headings become bullets.
    - Heading level controls nesting.
    - Paragraphs nest under the current heading.
    - Consecutive non-empty non-heading lines are joined into one paragraph.
    - Fenced code blocks are preserved as one nested block.
    """
    lines = markdown.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    current_heading_level = 0

    in_code = False
    code_lines: list[str] = []

    def emit_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(line.strip() for line in paragraph)
            level = current_heading_level + 1 if current_heading_level else 0
            out.append(f"{indent * level}- {text}")
            paragraph = []

    def emit_code() -> None:
        nonlocal code_lines
        if code_lines:
            level = current_heading_level + 1 if current_heading_level else 0
            out.append(f"{indent * level}- {code_lines[0]}")
            for line in code_lines[1:]:
                out.append(f"{indent * (level + 1)}{line}")
            code_lines = []

    for raw in lines:
        line = raw.rstrip()

        if line.startswith("```"):
            if in_code:
                code_lines.append(line)
                in_code = False
                emit_code()
            else:
                emit_paragraph()
                in_code = True
                code_lines = [line]
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            emit_paragraph()
            continue

        match = HEADING_RE.match(line)
        if match:
            emit_paragraph()
            hashes, title = match.groups()
            current_heading_level = len(hashes)
            out.append(f"{indent * (current_heading_level - 1)}- {hashes} {title}")
        else:
            paragraph.append(line)

    emit_paragraph()
    if in_code:
        emit_code()

    return "\n".join(out) + ("\n" if out else "")


def convert_file(src: str | Path, dst: str | Path | None = None) -> None:
    src = Path(src)
    result = md_to_logseq_outline(src.read_text(encoding="utf-8"))

    if dst is None:
        print(result, end="")
    else:
        Path(dst).write_text(result, encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()

    convert_file(args.src, args.output)
