from pathlib import Path
import re
import time
from tqdm import tqdm


# Allow indentation and a Logseq list marker before an opening fence.
opening = re.compile(r"^[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+)?(`{3,}|~{3,})(.*)$")
closing = re.compile(r"[ \t]*(`{3,}|~{3,})[ \t]*")


def convert_outside_fences(original):
    fence = None
    opened_at = None
    output = []
    count = 0

    for line_number, line in enumerate(original.splitlines(keepends=True), 1):
        body = line.rstrip("\r\n")

        if fence is not None:
            match = closing.fullmatch(body)
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence):
                fence = None
        else:
            match = opening.match(body)
            if match and (match[1][0] != "`" or "`" not in match[2]):
                fence = match[1]
                opened_at = line_number
            else:
                line, n = pattern.subn(r"[[\1]]", line)
                count += n

        output.append(line)

    if fence is not None:
        return original, 0, opened_at

    return "".join(output), count, None


def loop(root, write_changes):
    """
    Parameters
    ----------
    root: path to graph
    """
    # root = Path("/path/to/my-graph")

    # = True  # Change to True after reviewing the preview.

    pattern = re.compile(
        r"""(?<!\S)#([\w/-]+(?:\.[\w/-]+)*)(?=[,;.!?'":]*(?:\s|$))"""
    )

    for folder in tqdm( ("pages", "journals") ):
        for path in tqdm(sorted((root / folder).rglob("*.md")), leave=False):
            time.sleep(1)
            # Preserve existing newline characters.
            with path.open("r", encoding="utf-8", newline="") as f:
                original = f.read()

            converted, count, unclosed_at = convert_outside_fences(original)
            if unclosed_at is not None:
                print(f"SKIP {path.relative_to(root)}:{unclosed_at}: unclosed code fence")
                continue

            if not count:
                continue

            # print(f"{path.relative_to(root)}: {count} replacements")

            if write_changes:
                with path.open("w", encoding="utf-8", newline="") as f:
                    f.write(converted)

