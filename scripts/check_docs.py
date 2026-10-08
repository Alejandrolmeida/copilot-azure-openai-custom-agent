#!/usr/bin/env python3
"""Check local documentation links and parity of executable ES/EN examples."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
files = [*ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md"), *(ROOT / ".github").rglob("*.md")]
for path in files:
    text = path.read_text()
    for target in re.findall(r"\[[^]]*\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        destination = (path.parent / target.split("#", 1)[0]).resolve()
        if not destination.is_relative_to(ROOT) or not destination.exists():
            errors.append(f"{path.relative_to(ROOT)}: broken local link")
for spanish in (ROOT / "docs/es").glob("*.md"):
    english = ROOT / "docs" / spanish.name
    if not english.exists():
        errors.append(f"{spanish.name}: missing English guide")
        continue
    blocks = lambda file: re.findall(r"```[^\n]*\n(.*?)```", file.read_text(), re.S)
    if blocks(spanish) != blocks(english):
        errors.append(f"{spanish.name}: executable examples differ between languages")
for english in (ROOT / "docs").glob("*.md"):
    if not (ROOT / "docs/es" / english.name).exists():
        errors.append(f"{english.name}: missing Spanish guide")
print("\n".join(errors) if errors else "Documentation links and bilingual examples passed.")
sys.exit(bool(errors))
