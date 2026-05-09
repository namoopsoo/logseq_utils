# md_to_logseq.py
from __future__ import annotations

import re
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def md_to_logseq_outline(markdown: str, indent: str = "  ") -> str:
    out = []
    current_heading_level = 0
    in_code = False
    code_level = 0

    for raw in markdown.splitlines():
        line = raw.rstrip()

        if not line.strip():
            continue

        # fenced code block
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_level = current_heading_level + 1 if current_heading_level else 0
                out.append(f"{indent * code_level}- {line}")
            else:
                out.append(f"{indent * (code_level + 1)}{line}")
                in_code = False
            continue

        if in_code:
            out.append(f"{indent * (code_level + 1)}{line}")
            continue

        match = HEADING_RE.match(line)
        if match:
            hashes, title = match.groups()
            current_heading_level = len(hashes)
            out.append(f"{indent * (current_heading_level - 1)}- {hashes} {title}")
        else:
            level = current_heading_level + 1 if current_heading_level else 0
            out.append(f"{indent * level}- {line.strip()}")

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
