import argparse
import shutil
import unittest
from pathlib import Path

from notes_importer import cmd_auto


class TestNotesImporterAuto(unittest.TestCase):
    def test_cmd_auto_creates_expected_logseq_journals(self) -> None:
        root = Path(__file__).resolve().parent
        notes_dir = root / "notes_dir"
        staging_dir = root / "staging_dir"
        logseq_dir = root / "logseq_dir"

        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        if logseq_dir.exists():
            shutil.rmtree(logseq_dir)

        cmd_auto(
            argparse.Namespace(
                input_dir=str(notes_dir),
                staging_dir=str(staging_dir),
                logseq_dir=str(logseq_dir),
            )
        )

        self.assertTrue((logseq_dir / "journals" / "2026_01_15.md").exists())
        self.assertTrue((logseq_dir / "journals" / "2026_01_16.md").exists())
        self.assertTrue((logseq_dir / "assets" / "2026-01-15 note---inline-image.bin").exists())

        # cleanup 
        shutil.rmtree(logseq_dir)
        shutil.rmtree(staging_dir)


if __name__ == "__main__":
    unittest.main()
