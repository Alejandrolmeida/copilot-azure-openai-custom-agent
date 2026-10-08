#!/usr/bin/env python3
"""Build allowlisted client and optional importer artifacts; never bundle Git history."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import check_public

ROOT = check_public.ROOT


def zip_files(target, files):
    with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--allow-dirty", action="store_true", help="Build a NON-PUBLISHABLE validation snapshot")
    args = parser.parse_args()
    errors = check_public.check()
    if errors:
        raise ValueError("\n".join(errors))
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    if dirty and not args.allow_dirty:
        raise ValueError("Working tree is dirty; release requires an approved clean commit")
    files = {str(name): (ROOT / name).read_bytes() for name in check_public.public_files()}
    files["BUILD_INFO.json"] = json.dumps({
        "version": "2.0.0", "publishable": not dirty,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    }, indent=2).encode()
    files["SHA256SUMS"] = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n"
                                for name, data in sorted(files.items())).encode()
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / ("foundry-client-validation.zip" if dirty else "foundry-client-2.0.0.zip")
    zip_files(target, files)
    extension = {
        "extension/package.json": files["tools/vscode-import/package.json"],
        "extension/extension.js": files["tools/vscode-import/extension.js"],
        "extension/LICENSE": files["LICENSE"],
        "[Content_Types].xml": b'<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="json" ContentType="application/json"/><Default Extension="js" ContentType="application/javascript"/><Default Extension="vsixmanifest" ContentType="text/xml"/><Override PartName="/extension/LICENSE" ContentType="text/plain"/></Types>',
        "extension.vsixmanifest": b'<?xml version="1.0"?><PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011"><Metadata><Identity Language="en-US" Id="foundry-profile-import" Version="2.0.0" Publisher="community-foundry-client"/><DisplayName>Foundry Profile Import (Experimental)</DisplayName><Description xml:space="preserve">Explicit secure import</Description><Properties><Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.100.0"/></Properties></Metadata><Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation><Dependencies/><Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets></PackageManifest>',
    }
    vsix = args.output / "foundry-profile-import-2.0.0.vsix"
    zip_files(vsix, extension)
    for file in (target, vsix):
        print(hashlib.sha256(file.read_bytes()).hexdigest(), file.name)
    if dirty:
        print("Validation artifacts only: do not publish until the tree is committed and clean.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
