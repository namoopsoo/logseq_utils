import argparse
import base64
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

from md_to_logseq import convert_file



def find_matching_attachment(attachments_dir: Path, data_hash: str) -> Path | None:
    """Return the attachment file in ``attachments_dir`` matching ``data_hash``.

    ``data_hash`` is an md5 hash of the image bytes extracted from the base64
    encoded ``src`` value in the ``<img>`` tag.  ``attachments_dir`` may not
    exist; in that case ``None`` is returned.
    """
    if not attachments_dir.is_dir():
        return None

    for attachment in attachments_dir.iterdir():
        if attachment.is_file():
            file_hash = hashlib.md5(attachment.read_bytes()).hexdigest()
            if file_hash == data_hash:
                return attachment
    return None


IMAGE_MARKDOWN_PATH_RE = re.compile(r"(!\[[^\]]*\]\()(<[^>]*>|(?:[^()]|\([^()]*\))*)(\))")


def wrap_image_markdown_paths(text: str) -> str:
    """Wrap markdown image destinations in angle brackets.

    Markdown image links like ``![alt](../assets/file name (2).png)`` can
    contain spaces and parentheses in filenames. Logseq handles those paths more
    reliably when the destination is enclosed in ``<`` and ``>``. Already
    wrapped destinations are left unchanged.
    """

    def wrap_path(match: re.Match) -> str:
        prefix, path, suffix = match.groups()
        if path.startswith("<") and path.endswith(">"):
            return match.group(0)
        return f"{prefix}<{path}>{suffix}"

    return IMAGE_MARKDOWN_PATH_RE.sub(wrap_path, text)


def process_markdown(src_md: Path, dst_journals: Path, dst_assets: Path) -> None:
    """Copy ``src_md`` to ``dst_journals`` and replace embedded images.

    Embedded ``<img>`` tags with ``src="data:image/...;base64,..."`` are
    replaced with Logseq's image format after the corresponding attachment file
    is found and copied to ``dst_assets``.
    """
    base_name = src_md.stem
    attachments_dir = src_md.with_name(f"{base_name} Attachments")

    dst_file = dst_journals / src_md.name
    shutil.copy2(src_md, dst_file)
    text = dst_file.read_text()

    pattern = re.compile(r'<img[^>]+src="data:image/[^;]+;base64,([^\"]+)"[^>]*/>')

    def replace_img(match: re.Match) -> str:
        b64_data = match.group(1)
        img_bytes = base64.b64decode(b64_data)
        data_hash = hashlib.md5(img_bytes).hexdigest()
        attachment = find_matching_attachment(attachments_dir, data_hash)
        if attachment:
            asset_name = f"{base_name}---{attachment.name}"
            asset_path = dst_assets / asset_name
            shutil.copy2(attachment, asset_path)
            return wrap_image_markdown_paths(f"![image.png](../assets/{asset_name})")
        return match.group(0)

    new_text = re.sub(pattern, replace_img, text)
    dst_file.write_text(new_text)


def cmd_process_images(input_dir: str | Path, output_dir: str | Path) -> None:
    """Process markdown files replacing embedded images."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    journals_dir = output_dir / "processed_markdown"
    assets_dir = output_dir / "assets"
    journals_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    for md in sorted(input_dir.glob("*.md")):
        process_markdown(md, journals_dir, assets_dir)


def cmd_longdown(input_dir: str | Path, output_dir: str | Path) -> None:
    """Run longdown on markdown files."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    md_files = [p.name for p in sorted(input_dir.glob("*.md"))]

    for md_file in md_files:
        source_path = str(Path(input_dir) / md_file)
        destination_path = str(Path(output_dir) / md_file)

        convert_file(source_path, destination_path)
    ...


def cmd_append_to_logseq(input_dir: str | Path, logseq_dir: str | Path, assets_dir: str | Path) -> None:
    """Append markdown files and assets into a Logseq directory."""
    input_dir = Path(input_dir)
    assets_dir = Path(assets_dir)
    logseq_dir = Path(logseq_dir)

    journals_dir = logseq_dir / "journals"
    logseq_assets_dir = logseq_dir / "assets"
    journals_dir.mkdir(parents=True, exist_ok=True)
    logseq_assets_dir.mkdir(parents=True, exist_ok=True)

    # TODO Before proceeding, first gather what cannot be processed
    # but should do that in an earlier step before doing anything actually.

    for src_md in sorted(input_dir.glob("*.md")):
        match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", src_md.stem)
        if not match:
            print(f"Not processed (filename does not start with yyyy-mm-dd): {src_md.name}")
            continue

        yyyy, mm, dd = match.groups()
        dst_md = journals_dir / f"{yyyy}_{mm}_{dd}.md"
        append_text = src_md.read_text()
        if dst_md.exists():
            existing = dst_md.read_text()
        else:
            existing = ""

        with dst_md.open("a", encoding="utf-8") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            fh.write("- Imported below using [[app/Apple Notes Exporter]] and  [[logseq_utils/notes_importer.py]]\n")
            fh.write(append_text)
            if not append_text.endswith("\n"):
                fh.write("\n")

        # Delete src_md after finishing with it 
        print(f"deleting {src_md.absolute().as_posix()}")
        src_md.unlink()

    if assets_dir.exists():
        for asset in sorted(assets_dir.iterdir()):
            if asset.is_file():
                shutil.copy2(asset, logseq_assets_dir / asset.name)

                # unlink here too
                print(f"deleting {asset.absolute().as_posix()}")
                asset.unlink()
                ...
    ...


def cmd_auto(input_dir: str | Path, staging_dir: str | Path, logseq_dir: str | Path) -> None:
    """Run the full import pipeline: process-images -> longdown -> append-to-logseq."""
    input_dir = Path(input_dir)
    staging_dir = Path(staging_dir)
    logseq_dir = Path(logseq_dir)

    cmd_process_images(input_dir, staging_dir)

    cmd_longdown(staging_dir / "processed_markdown", staging_dir / "longdown")

    cmd_append_to_logseq(staging_dir / "longdown", logseq_dir, staging_dir / "assets")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import notes into Logseq")
    subparsers = parser.add_subparsers(dest="command", required=True)

    proc_parser = subparsers.add_parser("process-images", help="Replace embedded images with local assets")
    proc_parser.add_argument("--input-dir", required=True, help="Directory containing markdown files")
    proc_parser.add_argument("--output-dir", required=True, help="Directory for processed journals and assets")
    proc_parser.set_defaults(func=lambda args: cmd_process_images(args.input_dir, args.output_dir))

    longdown_parser = subparsers.add_parser("longdown", help="Run longdown on markdown files")
    longdown_parser.add_argument("--input-dir", required=True, help="Directory with markdown files")
    longdown_parser.add_argument("--output-dir", required=True, help="Directory for longdown output")
    longdown_parser.set_defaults(func=lambda args: cmd_longdown(args.input_dir, args.output_dir))

    append_parser = subparsers.add_parser("append-to-logseq", help="Append markdown and assets into a Logseq directory")
    append_parser.add_argument("--input-dir", required=True, help="Directory containing markdown files to append")
    append_parser.add_argument("--logseq-dir", required=True, help="Root Logseq directory")
    append_parser.add_argument("--assets-dir", required=True, help="Directory containing assets to copy")
    append_parser.set_defaults(func=lambda args: cmd_append_to_logseq(args.input_dir, args.logseq_dir, args.assets_dir))

    auto_parser = subparsers.add_parser(
        "auto",
        help="Run process-images, longdown, and append-to-logseq in sequence",
    )
    auto_parser.add_argument("--input-dir", required=True, help="Directory containing markdown files")
    auto_parser.add_argument("--logseq-dir", required=True, help="Root Logseq directory")
    auto_parser.add_argument("--staging-dir", required=True, help="Directory used for intermediate output")
    auto_parser.set_defaults(func=lambda args: cmd_auto(args.input_dir, args.staging_dir, args.logseq_dir))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
