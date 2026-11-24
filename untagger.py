from pathlib import Path
import re


TAG = re.compile(
    r"""(?<!\S)#(?:"""
    r"""(?P<bracketed>\[\[[^\[\]\r\n]+\]\])"""
    r"""|(?P<bare>[\w/-]+(?:\.[\w/-]+)*)(?=[,;.!?'":]*(?:\s|$))"""
    r")"
)

# Allow indentation and a Logseq list marker before an opening fence.
OPENING = re.compile(r"^[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+)?(`{3,}|~{3,})(.*)$")
CLOSING = re.compile(r"[ \t]*(`{3,}|~{3,})[ \t]*")


def convert_outside_fences(original: str) -> tuple[str, int, int | None]:
    """Return (converted text, replacement count, unclosed fence line or None).

    If a fence is unclosed, return the original text and zero replacements.
    The reported line number is one-based.
    """
    fence = None
    opened_at = None
    output = []
    count = 0

    for line_number, line in enumerate(original.splitlines(keepends=True), 1):
        body = line.rstrip("\r\n")

        if fence is not None:
            match = CLOSING.fullmatch(body)
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence):
                fence = None
        else:
            match = OPENING.match(body)
            if match and (match[1][0] != "`" or "`" not in match[2]):
                fence = match[1]
                opened_at = line_number
            else:
                line, n = TAG.subn(
                    lambda match: match["bracketed"] or f"[[{match['bare']}]]",
                    line,
                )
                count += n

        output.append(line)

    if fence is not None:
        return original, 0, opened_at

    return "".join(output), count, None


def loop(root: str | Path, write_changes: bool = False) -> None:
    """Preview or apply the conversion to a Logseq graph."""
    from tqdm import tqdm

    root = Path(root)
    for folder in ("pages", "journals"):
        paths = sorted((root / folder).rglob("*.md"))
        for path in tqdm(paths, desc=folder):
            with path.open("r", encoding="utf-8", newline="") as f:
                original = f.read()

            converted, count, unclosed_at = convert_outside_fences(original)
            relative = path.relative_to(root)
            if unclosed_at is not None:
                tqdm.write(f"SKIP {relative}:{unclosed_at}: unclosed code fence")
                continue
            if not count:
                continue

            if write_changes:
                with path.open("w", encoding="utf-8", newline="") as f:
                    f.write(converted)
            action = "UPDATED" if write_changes else "WOULD UPDATE"
            tqdm.write(f"{action} {relative}: {count} replacements")
