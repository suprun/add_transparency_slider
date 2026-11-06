# Rebuilding and updating the QGIS plugin

Requires Python 3.9+ and Git. Run the commands from the project root in PowerShell.

Rebuild the ZIP without changing the version:

```powershell
python -B scripts/package_plugin.py
```

Update existing copies in QGIS3/QGIS4 profiles:

```powershell
python -B scripts/sync_to_qgis_profiles.py
```

Rebuild and update only if the build succeeds:

```powershell
python -B scripts/package_plugin.py
if ($LASTEXITCODE -eq 0) { python -B scripts/sync_to_qgis_profiles.py }
```

Rebuild and update while QGIS is running (PowerShell 7+):

```powershell
python -B scripts/package_plugin.py && python -B scripts/sync_to_qgis_profiles.py --allow-running-qgis
```

Close QGIS before updating. To update while QGIS is running, add
`--allow-running-qgis`, then restart QGIS or reload the plugin using
Plugin Reloader.

- `package_plugin.py --bump` - increment the fourth version component in
  `metadata.txt` and `repo/plugins.xml`, then create the ZIP.
- `--dry-run` - preview package contents or target profiles without writing files.
- `sync_to_qgis_profiles.py --qgis-root "D:/QGIS"` - use a different profiles root.
- `--backup-root` - use a different backup directory on the same drive as the profiles.

ZIP: `repo/add_transparency_slider.zip`. Before updating, the script checks
ZIP integrity, versions, and file contents against the source files. If the
source files have changed, rebuild the package first. The `scripts` directory
is excluded from the ZIP.

Backups: `%LOCALAPPDATA%/Codex/plugin-backups/add_transparency_slider-<timestamp>`.
The exact path is printed after updating. Profile settings remain unchanged.
To restore a backup, close QGIS, move the current plugin directory elsewhere,
and return the backup directory to its original location. If replacement or
verification fails for a profile, the script automatically restores its
previous copy.

Test the scripts:

```powershell
python -B -m unittest discover -s scripts -p test_release_tools.py -v
```
