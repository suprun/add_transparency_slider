"""Build and verify the plugin archive using the existing repacker."""

import argparse
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import repack  # noqa: E402


def verify_archive() -> dict:
    """Return archive contents after checking versions and source equality."""
    version = repack.get_current_version()
    entry = ET.parse(repack.PLUGINS_XML).getroot().find("pyqgis_plugin")
    if (entry is None or entry.get("version") != version
            or entry.findtext("version") != version):
        raise ValueError("metadata.txt and plugins.xml versions differ")
    patterns = repack.load_gitignore_patterns(str(ROOT))
    files = repack.collect_plugin_files(str(ROOT), patterns)
    expected = {f"{repack.PLUGIN_NAME}/{name}" for name in files}
    with zipfile.ZipFile(repack.DEFAULT_ZIP) as archive:
        names = archive.namelist()
        if len(names) != len(expected) or set(names) != expected:
            raise ValueError("Archive file list differs from source")
        if archive.testzip() is not None:
            raise ValueError("Archive CRC check failed")
        payload = {}
        for name in files:
            parts = name.split("/")
            if any(part in ("", ".", "..") or ":" in part
                   or "\\" in part for part in parts):
                raise ValueError(f"Unsafe archive path: {name}")
            content = archive.read(f"{repack.PLUGIN_NAME}/{name}")
            if content != (ROOT / name).read_bytes():
                raise ValueError(f"Archive differs from source: {name}")
            payload[name] = content
    print(f"Verified: version={version}; files={len(payload)}; CRC_OK")
    return payload


def main() -> int:
    """Build without changing the version unless --bump is supplied."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bump", action="store_true",
                        help="Increment the fourth version component")
    parser.add_argument("--dry-run", action="store_true",
                        help="List package files without writing anything")
    args = parser.parse_args()
    if args.dry_run and args.bump:
        parser.error("--dry-run cannot be combined with --bump")
    command = [sys.executable, "-B", str(ROOT / "repack.py")]
    if args.bump:
        command.append("--bump")
    if args.dry_run:
        command.append("--dry-run")
    subprocess.run(command, check=True, cwd=str(ROOT))
    if not args.dry_run:
        verify_archive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
