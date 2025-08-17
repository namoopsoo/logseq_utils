import argparse
import base64
import hashlib
import re
import shutil
import subprocess
from pathlib import Path


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
            return f"![image.png](../assets/{asset_name})"
        return match.group(0)

    new_text = re.sub(pattern, replace_img, text)
    dst_file.write_text(new_text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import notes into Logseq")
    parser.add_argument("--input-folder", required=True, help="Folder containing markdown files")
    parser.add_argument("--prefix", default="", help="Optional filename prefix filter")
    parser.add_argument("--intermediary-dir-one", required=True, help="First intermediary directory")
    parser.add_argument("--intermediary-dir-two", required=True, help="Second intermediary directory")
    parser.add_argument("--dry-run", action="store_true", help="Print files without processing")
    args = parser.parse_args()

    input_path = Path(args.input_folder)
    md_files = sorted(p for p in input_path.glob("*.md") if not args.prefix or p.name.startswith(args.prefix))

    if args.dry_run:
        for p in md_files:
            print(p)
        return

    journals_dir_one = Path(args.intermediary_dir_one) / "journals"
    assets_dir_one = Path(args.intermediary_dir_one) / "assets"
    journals_dir_two = Path(args.intermediary_dir_two) / "journals"
    journals_dir_one.mkdir(parents=True, exist_ok=True)
    assets_dir_one.mkdir(parents=True, exist_ok=True)
    journals_dir_two.mkdir(parents=True, exist_ok=True)

    for md in md_files:
        process_markdown(md, journals_dir_one, assets_dir_one)

    cmd = ["longdown", "-d", str(journals_dir_two)] + [str(p) for p in journals_dir_one.glob("*.md")]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
