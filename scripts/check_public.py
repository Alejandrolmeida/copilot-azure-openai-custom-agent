#!/usr/bin/env python3
"""Publication boundary check. Reports categories and paths, never matched values."""
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = {".github", "docs", "examples", "scripts", "tests", "infra", "tools", "schemas"}
FILES = {"README.md", "README.es.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md",
         "CHANGELOG.md", ".gitignore", ".gitattributes", ".markdownlint.json",
         "package.json", "package-lock.json", "bicepconfig.json"}
PUBLIC_ROLE_IDS = {"4633458b-17de-408a-b874-0445c86b69e6"}
SYNTHETIC_HOSTS = {"oai-example.openai.azure.com", "different.openai.azure.com",
                   "oai.openai.azure.com", "example.openai.azure.com"}
ARCHITECTURE_DOC = Path("docs/arquitectura-copilot-azure-openai.docx")
DOCX_PARTS = {
    "[Content_Types].xml", "_rels/.rels", "docProps/core.xml", "docProps/app.xml",
    "word/document.xml", "word/_rels/document.xml.rels",
    "word/styles.xml", "word/stylesWithEffects.xml", "word/settings.xml",
    "word/webSettings.xml", "word/fontTable.xml", "word/theme/theme1.xml",
    "word/numbering.xml", "word/media/image1.png", "word/media/image2.png",
}


def findings(text):
    result = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for value in re.findall(r"\b[a-fA-F0-9]{8}-(?:[a-fA-F0-9]{4}-){3}[a-fA-F0-9]{12}\b", line):
            if not value.startswith("00000000-") and value not in PUBLIC_ROLE_IDS:
                result.append((line_number, "non-synthetic-identity"))
        for host in re.findall(r"\b[a-z0-9-]+\.(?:openai\.azure\.com|vault\.azure\.net)\b", line):
            if host not in SYNTHETIC_HOSTS and host != "kv-example.vault.azure.net":
                result.append((line_number, "operational-host"))
        for email in re.findall(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b", line):
            if email not in ("example.com", "example.org", "example.net", "example.openai.azure.com"):
                result.append((line_number, "personal-email"))
        if re.search(r"(?:/home/[a-z][a-z0-9_-]+/|/mnt/c/Users/[A-Za-z0-9._-]+/)", line):
            result.append((line_number, "personal-path"))
    return result


def candidates():
    result = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"],
                            cwd=ROOT, capture_output=True, check=True)
    return sorted({Path(name.decode()) for name in result.stdout.split(b"\0") if name})


def inspect_architecture_doc(path):
    errors = []
    with ZipFile(path) as archive:
        members = archive.infolist()
        names = [item.filename for item in members]
        if len(names) != len(set(names)) or set(names) != DOCX_PARTS:
            raise ValueError(f"Unexpected or missing Word part: {ARCHITECTURE_DOC}")
        if sum(item.file_size for item in members) > 2_000_000 or any(
                item.file_size > 500_000 or item.flag_bits & 1 for item in members):
            raise ValueError(f"Oversized or encrypted Word part: {ARCHITECTURE_DOC}")
        if archive.testzip() is not None:
            raise ValueError(f"Corrupt Word archive: {ARCHITECTURE_DOC}")
        for member in members:
            if not member.filename.endswith((".xml", ".rels")):
                continue
            root = ET.fromstring(archive.read(member))
            text = "\n".join([value for node in root.iter() for value in
                              (*node.attrib.values(), node.text or "")])
            if member.filename == "word/document.xml":
                word = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                text += "\n" + "\n".join(
                    "".join(node.text or "" for node in paragraph.iter(f"{word}t"))
                    for paragraph in root.iter(f"{word}p")
                )
            if member.filename.endswith(".rels") and any(
                    node.attrib.get("TargetMode") == "External" for node in root):
                raise ValueError(f"External Word relationship: {ARCHITECTURE_DOC}")
            errors.extend(f"{ARCHITECTURE_DOC}:{member.filename}:{line}: {category}"
                          for line, category in findings(text))
    return errors


def public_files():
    selected = []
    for relative in candidates():
        file = ROOT / relative
        if not file.exists():
            continue
        if file.is_symlink() or any(parent.is_symlink() for parent in file.parents):
            raise ValueError(f"Symlink not allowed in publication: {relative}")
        if relative.parts[0] not in DIRECTORIES and str(relative) not in FILES:
            raise ValueError(f"File outside publication allowlist: {relative}")
        if relative.suffix in (".db", ".sqlite", ".vscdb", ".eml", ".zip", ".vsix", ".log"):
            raise ValueError(f"Private/generated artifact in source tree: {relative}")
        if relative.suffix == ".docx" and relative != ARCHITECTURE_DOC:
            raise ValueError(f"Unreviewed Word document: {relative}")
        selected.append(relative)
    return selected


def check():
    errors = []
    for relative in public_files():
        if relative == ARCHITECTURE_DOC:
            errors.extend(inspect_architecture_doc(ROOT / relative))
        else:
            text = (ROOT / relative).read_text(encoding="utf-8")
            errors.extend(f"{relative}:{line}: {category}" for line, category in findings(text))
    return errors


if __name__ == "__main__":
    try:
        errors = check()
        print("\n".join(errors) if errors else "Publication boundary check passed (not a secret scanner).")
        sys.exit(bool(errors))
    except (ValueError, OSError, BadZipFile, ET.ParseError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
