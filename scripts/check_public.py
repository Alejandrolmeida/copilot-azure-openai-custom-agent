#!/usr/bin/env python3
"""Publication boundary check. Reports categories and paths, never matched values."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = {".github", "docs", "examples", "scripts", "tests", "infra", "tools", "schemas"}
FILES = {"README.md", "README.es.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md",
         "CHANGELOG.md", ".gitignore", ".gitattributes", ".markdownlint.json",
         "package.json", "package-lock.json", "bicepconfig.json"}
PUBLIC_ROLE_IDS = {"4633458b-17de-408a-b874-0445c86b69e6"}
SYNTHETIC_HOSTS = {"oai-example.openai.azure.com", "different.openai.azure.com",
                   "oai.openai.azure.com", "example.openai.azure.com"}


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
        selected.append(relative)
    return selected


def check():
    errors = []
    for relative in public_files():
        text = (ROOT / relative).read_text(encoding="utf-8")
        errors.extend(f"{relative}:{line}: {category}" for line, category in findings(text))
    return errors


if __name__ == "__main__":
    try:
        errors = check()
        print("\n".join(errors) if errors else "Publication boundary check passed (not a secret scanner).")
        sys.exit(bool(errors))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
