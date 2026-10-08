#!/usr/bin/env python3
"""Verify a client archive, then run offline tests from an isolated extraction."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile

import check_public


def verify(archive_path):
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive paths")
        for name in names:
            relative = PurePosixPath(name)
            if relative.is_absolute() or ".." in relative.parts or "\\" in name:
                raise ValueError("Unsafe archive path")
            if name not in {"BUILD_INFO.json", "SHA256SUMS"} and (
                relative.parts[0] not in check_public.DIRECTORIES and name not in check_public.FILES
            ):
                raise ValueError("Unexpected archive entry")
            issues = check_public.findings(archive.read(name).decode("utf-8"))
            if issues:
                raise ValueError(f"Private metadata in archive: {name}")
        checked = set()
        for line in archive.read("SHA256SUMS").decode().splitlines():
            digest, name = line.split("  ", 1)
            if name in checked or hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError("Invalid or duplicated checksum")
            checked.add(name)
        if checked != set(names) - {"SHA256SUMS"}:
            raise ValueError("Checksum manifest does not cover the entire archive")
        metadata = json.loads(archive.read("BUILD_INFO.json"))
        with tempfile.TemporaryDirectory(prefix="foundry-clean-client-") as folder:
            archive.extractall(folder)
            subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                           cwd=folder, check=True)
            subprocess.run(["node", "--test", "tests/vscode-import.test.cjs"], cwd=folder, check=True)
            subprocess.run([sys.executable, "scripts/check_docs.py"], cwd=folder, check=True)
            subprocess.run([sys.executable, "scripts/foundry.py", "--help"], cwd=folder,
                           stdout=subprocess.DEVNULL, check=True)
        return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.archive), indent=2))
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
