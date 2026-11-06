"""Focused checks for release verification and profile recovery."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import package_plugin
import sync_to_qgis_profiles as sync


class ReleaseToolsTests(unittest.TestCase):
    def test_package_matches_sources(self) -> None:
        payload = package_plugin.verify_archive()
        self.assertIn("metadata.txt", payload)
        self.assertTrue(any(name.endswith(".qm") for name in payload))
        self.assertFalse(any(name.startswith("scripts/") for name in payload))

    def test_stale_archive_is_rejected(self) -> None:
        with patch.object(package_plugin.repack, "collect_plugin_files",
                          return_value=["metadata.txt"]):
            with self.assertRaisesRegex(ValueError, "file list"):
                package_plugin.verify_archive()

    def test_version_mismatch_is_rejected(self) -> None:
        with patch.object(package_plugin.repack, "get_current_version",
                          return_value="invalid"):
            with self.assertRaisesRegex(ValueError, "versions differ"):
                package_plugin.verify_archive()

    def test_crc_failure_is_rejected(self) -> None:
        with patch.object(zipfile.ZipFile, "testzip", return_value="bad"):
            with self.assertRaisesRegex(ValueError, "CRC"):
                package_plugin.verify_archive()

    def test_update_preserves_backup(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "plugin"
            saved = Path(folder) / "backup" / "plugin"
            target.mkdir()
            (target / "old.txt").write_bytes(b"previous")
            payload = {"metadata.txt": b"new", "i18n/uk.qm": b"translation"}
            sync.sync_profile(target, saved, payload)
            self.assertEqual((saved / "old.txt").read_bytes(), b"previous")
            self.assertFalse((target / "old.txt").exists())
            for name, content in payload.items():
                self.assertEqual((target / name).read_bytes(), content)

    def test_failed_replacement_restores_previous_copy(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "plugin"
            saved = Path(folder) / "backup" / "plugin"
            target.mkdir()
            (target / "old.txt").write_bytes(b"previous")
            original_rename = Path.rename

            def fail_stage(path: Path, destination: Path) -> Path:
                if ".staging-" in path.name:
                    raise OSError("Simulated installation failure")
                return original_rename(path, destination)

            with patch.object(Path, "rename", fail_stage):
                with self.assertRaisesRegex(OSError, "Simulated"):
                    sync.sync_profile(target, saved, {"new.txt": b"new"})
            self.assertEqual((target / "old.txt").read_bytes(), b"previous")
            self.assertFalse(saved.exists())

    def test_process_detection(self) -> None:
        result = type("Result", (), {"stdout": '"qgis-ltr-bin.exe","123"'})()
        with patch.object(sync.subprocess, "run", return_value=result):
            with patch.object(sync.os, "name", "nt"):
                self.assertTrue(sync.qgis_is_running())


if __name__ == "__main__":
    unittest.main()
