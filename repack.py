#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repack script for the 'Add Transparency Slider' QGIS plugin.

Packages the plugin files into repo/add_transparency_slider.zip according
to QGIS plugin repository specifications, excluding __pycache__, repository
artifacts, internal instructions, and patterns from .gitignore.
"""

import argparse
import fnmatch
import os
import re
import sys
import zipfile

PLUGIN_NAME = "add_transparency_slider"
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
METADATA_FILE = os.path.join(ROOT_DIR, "metadata.txt")
REPO_DIR = os.path.join(ROOT_DIR, "repo")
PLUGINS_XML = os.path.join(REPO_DIR, "plugins.xml")
DEFAULT_ZIP = os.path.join(REPO_DIR, f"{PLUGIN_NAME}.zip")

# Directories to always skip
IGNORED_DIRS = {
    ".git",
    "repo",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    ".idea",
    ".vscode",
}

# Explicit file patterns to always skip from the plugin package
IGNORED_PATTERNS = {
    "repack.py",
    "AGENTS.md",
    ".gitignore",
    "*.zip",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.qm",
    "transparency.svg",
    "*.log",
    "*.env",
    ".env.*",
    "Thumbs.db",
    "desktop.ini",
    ".DS_Store",
}


def load_gitignore_patterns(root_dir):
    """Load ignore patterns from .gitignore."""
    gitignore_path = os.path.join(root_dir, ".gitignore")
    patterns = set(IGNORED_PATTERNS)
    if not os.path.exists(gitignore_path):
        return patterns

    with open(gitignore_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Remove trailing slash for directory patterns
            pat = line.rstrip("/")
            patterns.add(pat)
    return patterns


def should_include(rel_path, ignore_patterns):
    """Determine whether a relative file path should be included in the zip."""
    parts = rel_path.replace("\\", "/").split("/")
    # Check if any parent directory is in IGNORED_DIRS
    for part in parts[:-1]:
        if part in IGNORED_DIRS:
            return False

    filename = parts[-1]
    # Check patterns against filename and relative path
    for pat in ignore_patterns:
        if fnmatch.fnmatch(filename, pat) or fnmatch.fnmatch(rel_path, pat):
            return False
        # Match directory pattern against any component
        for part in parts:
            if fnmatch.fnmatch(part, pat):
                return False

    return True


def collect_plugin_files(root_dir, ignore_patterns):
    """Collect all files belonging to the plugin."""
    # If in a git repository, start with tracked files (excludes local untracked scratch files)
    try:
        import subprocess

        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        tracked = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
        files = [
            f for f in tracked
            if should_include(f, ignore_patterns) and os.path.isfile(os.path.join(root_dir, f))
        ]
        if files:
            return sorted(files)
    except Exception:
        pass

    # Fallback to filesystem traversal
    files = []
    for root, dirs, filenames in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for name in filenames:
            abs_path = os.path.join(root, name)
            rel_path = os.path.relpath(abs_path, root_dir).replace("\\", "/")
            if should_include(rel_path, ignore_patterns):
                files.append(rel_path)

    return sorted(files)


def get_current_version():
    """Read current version from metadata.txt."""
    if not os.path.exists(METADATA_FILE):
        return "unknown"
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("version="):
                return line.strip().split("=", 1)[1]
    return "unknown"


def increment_build_number():
    """Increment the 4th digit (build number) in metadata.txt and repo/plugins.xml."""
    curr_version = get_current_version()
    parts = curr_version.split(".")
    if len(parts) != 4:
        print(f"Warning: version '{curr_version}' does not have 4 parts (major.minor.patch.build).")
        return curr_version

    try:
        build_num = int(parts[3]) + 1
        new_version = f"{parts[0]}.{parts[1]}.{parts[2]}.{build_num}"
    except ValueError:
        print(f"Warning: could not parse build number from '{curr_version}'.")
        return curr_version

    # Update metadata.txt
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(r"^version=.*$", f"version={new_version}", content, flags=re.MULTILINE)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    # Update repo/plugins.xml if exists
    if os.path.exists(PLUGINS_XML):
        with open(PLUGINS_XML, "r", encoding="utf-8") as f:
            xml_content = f.read()
        xml_content = re.sub(
            r'version="[^"]*"',
            f'version="{new_version}"',
            xml_content,
            count=1,
        )
        xml_content = re.sub(
            r"<version>[^<]*</version>",
            f"<version>{new_version}</version>",
            xml_content,
            count=1,
        )
        with open(PLUGINS_XML, "w", encoding="utf-8") as f:
            f.write(xml_content)

    print(f"Incremented version: {curr_version} -> {new_version}")
    return new_version


def create_zip(files, output_zip):
    """Package the files into a clean zip archive."""
    os.makedirs(os.path.dirname(os.path.abspath(output_zip)), exist_ok=True)
    temp_zip = output_zip + ".tmp"

    with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in files:
            arcname = f"{PLUGIN_NAME}/{rel}"
            abs_path = os.path.join(ROOT_DIR, rel)
            z.write(abs_path, arcname)

    if os.path.exists(output_zip):
        os.remove(output_zip)
    os.rename(temp_zip, output_zip)


def main():
    parser = argparse.ArgumentParser(description="Repack QGIS plugin into repo/add_transparency_slider.zip")
    parser.add_argument(
        "--bump",
        action="store_true",
        help="Increment build number in metadata.txt and repo/plugins.xml before repacking",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=DEFAULT_ZIP,
        help=f"Output zip path (default: {os.path.relpath(DEFAULT_ZIP, ROOT_DIR)})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print files to be included without creating archive",
    )
    args = parser.parse_args()

    if args.bump:
        version = increment_build_number()
    else:
        version = get_current_version()

    ignore_patterns = load_gitignore_patterns(ROOT_DIR)
    files = collect_plugin_files(ROOT_DIR, ignore_patterns)

    if args.dry_run:
        print(f"Plugin version: {version}")
        print(f"Dry run: {len(files)} files will be packaged into '{args.output}':")
        for f in files:
            print(f"  {PLUGIN_NAME}/{f}")
        return 0

    create_zip(files, args.output)
    size_bytes = os.path.getsize(args.output)
    print(f"Successfully packaged {len(files)} files (v{version}) into:")
    print(f"  {args.output} ({size_bytes:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
