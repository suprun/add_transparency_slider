"""Install the verified ZIP into existing QGIS profiles with backups."""

import argparse
import csv
from datetime import datetime
import os
from pathlib import Path
import subprocess
import sys
import uuid

from package_plugin import verify_archive

PLUGIN_NAME = "add_transparency_slider"


def qgis_is_running() -> bool:
    """Check Windows QGIS processes without reading command lines."""
    if os.name != "nt":
        return False
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"], capture_output=True,
        text=True, check=True,
    )
    return any(row and row[0].lower().startswith("qgis")
               and row[0].lower().endswith(".exe")
               for row in csv.reader(result.stdout.splitlines()))


def sync_profile(target: Path, saved: Path, payload: dict) -> None:
    """Replace one installed copy, restoring it if verification fails."""
    stage = target.with_name(f"{PLUGIN_NAME}.staging-{uuid.uuid4().hex}")
    stage.mkdir()
    for name, content in payload.items():
        output = stage / name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)
    saved.parent.mkdir(parents=True, exist_ok=True)
    target.rename(saved)
    try:
        stage.rename(target)
        actual = {p.relative_to(target).as_posix(): p.read_bytes()
                  for p in target.rglob("*") if p.is_file()}
        if actual != payload:
            raise ValueError(f"Installed files differ from ZIP: {target}")
    except (OSError, ValueError):
        if target.exists():
            target.rename(stage.with_name(stage.name + "-failed"))
        saved.rename(target)
        raise
    print(f"Updated: {target}; files={len(payload)}; differences=0")


def main() -> int:
    """Update existing copies only; preserve settings and previous files."""
    parser = argparse.ArgumentParser(description=__doc__)
    appdata = Path(os.environ.get("APPDATA", str(Path.home() / ".config")))
    localdata = Path(os.environ.get("LOCALAPPDATA", str(appdata)))
    parser.add_argument("--qgis-root", type=Path, default=appdata / "QGIS",
                        help="QGIS root containing QGIS3/QGIS4 profiles")
    parser.add_argument("--backup-root", type=Path,
                        default=localdata / "Codex" / "plugin-backups",
                        help="Backup root on the same drive as the profiles")
    parser.add_argument("--dry-run", action="store_true",
                        help="Verify ZIP and list targets without writing")
    parser.add_argument("--allow-running-qgis", action="store_true",
                        help="Update files while QGIS is open; restart afterward")
    args = parser.parse_args()
    payload = verify_archive()
    profiles = args.qgis_root.resolve()
    targets = sorted(profiles.glob(
        f"QGIS*/profiles/*/python/plugins/{PLUGIN_NAME}"
    ))
    if not targets:
        raise FileNotFoundError(f"No installed copies found under {profiles}")
    for target in targets:
        if target.is_symlink() or not target.resolve().is_relative_to(profiles):
            raise ValueError(f"Profile target escapes QGIS root: {target}")
    if args.dry_run:
        for target in targets:
            print(f"Would update: {target}")
        return 0
    if qgis_is_running() and not args.allow_running_qgis:
        raise RuntimeError("Close QGIS or use --allow-running-qgis, then restart")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = args.backup_root.resolve() / f"{PLUGIN_NAME}-{stamp}"
    for target in targets:
        target = target.resolve()
        sync_profile(target, backup / target.relative_to(profiles), payload)
    print(f"Backups: {backup}")
    print("Restart QGIS or reload the plugin to apply the update.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
