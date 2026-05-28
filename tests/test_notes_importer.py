import sys
from pathlib import Path
from unittest.mock import MagicMock, call

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import notes_importer


def test_find_matching_attachment_returns_none_when_dir_missing(tmp_path: Path) -> None:
    assert notes_importer.find_matching_attachment(tmp_path / "missing", "abc") is None


def test_find_matching_attachment_returns_matching_file(tmp_path: Path) -> None:
    attachments_dir = tmp_path / "note Attachments"
    attachments_dir.mkdir()
    (attachments_dir / "other.bin").write_bytes(b"other")
    target = attachments_dir / "target.bin"
    target_bytes = b"match me"
    target.write_bytes(target_bytes)
    data_hash = notes_importer.hashlib.md5(target_bytes).hexdigest()
    assert notes_importer.find_matching_attachment(attachments_dir, data_hash) == target


def test_process_markdown_replaces_embedded_image_and_copies_attachment(tmp_path: Path) -> None:
    src_md = tmp_path / "2026-01-16 note.md"
    src_md.write_text('<img src="data:image/png;base64,YWJj"/>')
    attachments_dir = tmp_path / "2026-01-16 note Attachments"
    attachments_dir.mkdir()
    (attachments_dir / "inline-image.bin").write_bytes(b"abc")
    dst_journals = tmp_path / "journals"
    dst_assets = tmp_path / "assets"
    dst_journals.mkdir()
    dst_assets.mkdir()

    notes_importer.process_markdown(src_md, dst_journals, dst_assets)

    output = (dst_journals / src_md.name).read_text()
    assert "![image.png](../assets/2026-01-16 note---inline-image.bin)" in output
    assert (dst_assets / "2026-01-16 note---inline-image.bin").exists()


def test_cmd_process_images_uses_expected_paths(monkeypatch) -> None:
    process_mock = MagicMock()
    monkeypatch.setattr(notes_importer, "process_markdown", process_mock)
    input_dir = Path("/tmp/in")
    output_dir = Path("/tmp/out")
    mkdir_mock = MagicMock()
    monkeypatch.setattr(Path, "glob", lambda self, pattern: [input_dir / "b.md", input_dir / "a.md"] if self == input_dir else [])
    monkeypatch.setattr(Path, "mkdir", lambda self, parents=False, exist_ok=False: mkdir_mock(self, parents, exist_ok))

    notes_importer.cmd_process_images(str(input_dir), str(output_dir))

    journals_dir = output_dir / "processed_markdown"
    assets_dir = output_dir / "assets"
    mkdir_mock.assert_has_calls([call(journals_dir, True, True), call(assets_dir, True, True)])
    process_mock.assert_has_calls([call(input_dir / "a.md", journals_dir, assets_dir), call(input_dir / "b.md", journals_dir, assets_dir)])


def test_cmd_longdown_converts_each_markdown(monkeypatch) -> None:
    convert_mock = MagicMock()
    monkeypatch.setattr(notes_importer, "convert_file", convert_mock)
    input_dir = Path("/tmp/in")
    output_dir = Path("/tmp/out")
    monkeypatch.setattr(Path, "mkdir", lambda self, parents=False, exist_ok=False: None)
    monkeypatch.setattr(Path, "glob", lambda self, pattern: [input_dir / "z.md", input_dir / "a.md"] if self == input_dir else [])

    notes_importer.cmd_longdown(str(input_dir), str(output_dir))

    assert convert_mock.call_args_list == [call(str(input_dir / "a.md"), str(output_dir / "a.md")), call(str(input_dir / "z.md"), str(output_dir / "z.md"))]


def test_cmd_append_to_logseq_appends_and_moves_assets(tmp_path: Path) -> None:
    input_dir = tmp_path / "longdown"
    input_dir.mkdir()
    src_md = input_dir / "2026-01-15 note.md"
    src_md.write_text("content")
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    asset = assets_dir / "img.bin"
    asset.write_bytes(b"img")
    logseq_dir = tmp_path / "logseq"

    notes_importer.cmd_append_to_logseq(str(input_dir), str(logseq_dir), str(assets_dir))

    dst_md = logseq_dir / "journals" / "2026_01_15.md"
    assert dst_md.exists()
    assert "Imported below" in dst_md.read_text()
    assert (logseq_dir / "assets" / "img.bin").exists()
    assert not src_md.exists()
    assert not asset.exists()


def test_cmd_auto_chains_commands(monkeypatch) -> None:
    process_mock = MagicMock()
    longdown_mock = MagicMock()
    append_mock = MagicMock()
    monkeypatch.setattr(notes_importer, "cmd_process_images", process_mock)
    monkeypatch.setattr(notes_importer, "cmd_longdown", longdown_mock)
    monkeypatch.setattr(notes_importer, "cmd_append_to_logseq", append_mock)

    notes_importer.cmd_auto("/in", "/staging", "/logseq")

    process_mock.assert_called_once_with(Path("/in"), Path("/staging"))
    longdown_mock.assert_called_once_with(Path("/staging/processed_markdown"), Path("/staging/longdown"))
    append_mock.assert_called_once_with(Path("/staging/longdown"), Path("/logseq"), Path("/staging/assets"))


def test_process_markdown_converts_heic_attachment_to_jpeg(tmp_path: Path, monkeypatch) -> None:
    src_md = tmp_path / "2026-01-16 note.md"
    src_md.write_text('<img src="data:image/heic;base64,YWJj"/>')
    attachments_dir = tmp_path / "2026-01-16 note Attachments"
    attachments_dir.mkdir()
    (attachments_dir / "inline-image.heic").write_bytes(b"abc")
    dst_journals = tmp_path / "journals"
    dst_assets = tmp_path / "assets"
    dst_journals.mkdir()
    dst_assets.mkdir()

    run_mock = MagicMock()
    monkeypatch.setattr(notes_importer.subprocess, "run", run_mock)

    notes_importer.process_markdown(src_md, dst_journals, dst_assets)

    output = (dst_journals / src_md.name).read_text()
    assert "![image.png](../assets/2026-01-16 note---inline-image.jpeg)" in output
    run_mock.assert_called_once()
