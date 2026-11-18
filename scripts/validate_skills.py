#!/usr/bin/env python3
"""Validate every skill against the Agent Skills format and packaging rules.

  python3 scripts/validate_skills.py

Checks: frontmatter (name matches folder, lowercase-hyphen, <= 64 chars;
description 1-1024 chars; compatibility <= 500), SKILL.md under 500 lines,
every referenced references/ file exists, text files only (no executables or
binaries), no kit placeholders, no secrets, licence matches skills.json,
references in sync with the kit. Exit 0 = pass. Stdlib only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TEXT_EXT = {".md", ".txt", ".json", ".yaml", ".yml"}
SECRET = re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}|\bgh[pousr]_[A-Za-z0-9]{30,}|\bAKIA[0-9A-Z]{16}\b|-----BEGIN [A-Z ]*PRIVATE KEY-----")
# Token budgets. Every installed skill's description is loaded at the start of
# every session, and SKILL.md is loaded whenever the skill runs, so both are
# loaded repeatedly. Raise these only with a measured reason.
MAX_DESCRIPTION_CHARS = 420   # long enough for explicit trigger phrases (measured: shorter ones missed triggers)
MAX_SKILL_TOKENS = 1600          # estimated as characters / 4
errors: list[str] = []


def frontmatter(text: str) -> tuple[dict[str, str], str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    fm: dict[str, str] = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([a-z][a-z0-9_-]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm, text[end + 5:]


def main() -> int:
    cfg = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
    dirs = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    names = {d.name for d in dirs}
    for missing in sorted(set(cfg["skills"]) - names):
        errors.append(f"skills.json lists '{missing}' but skills/{missing}/ does not exist")
    for extra in sorted(names - set(cfg["skills"])):
        errors.append(f"skills/{extra}/ is not listed in skills.json")
    stamps = set()
    for d in dirs:
        rel = f"skills/{d.name}"
        skill = d / "SKILL.md"
        if not skill.is_file():
            errors.append(f"{rel}: SKILL.md missing")
            continue
        text = skill.read_text(encoding="utf-8")
        parsed = frontmatter(text)
        if not parsed:
            errors.append(f"{rel}/SKILL.md: missing or malformed YAML frontmatter")
            continue
        fm, body = parsed
        name = fm.get("name", "")
        if name != d.name:
            errors.append(f"{rel}: frontmatter name '{name}' must equal folder name")
        if not NAME.match(name) or len(name) > 64:
            errors.append(f"{rel}: name must be lowercase letters/digits/hyphens, <= 64 chars")
        desc = fm.get("description", "")
        if not 1 <= len(desc) <= 1024:
            errors.append(f"{rel}: description must be 1-1024 chars (is {len(desc)})")
        elif len(desc) > MAX_DESCRIPTION_CHARS:
            errors.append(f"{rel}: description is {len(desc)} chars; budget is {MAX_DESCRIPTION_CHARS} (it loads in every session)")
        if len(text) // 4 > MAX_SKILL_TOKENS:
            errors.append(f"{rel}: SKILL.md is ~{len(text) // 4} tokens; budget is {MAX_SKILL_TOKENS} — move detail into references/")
        if not re.search(r'^\s+version:\s*"?\d+\.\d+\.\d+"?\s*$', text, re.M):
            errors.append(f"{rel}: metadata.version (semver) is required")
        if "use when" not in desc.lower():
            errors.append(f"{rel}: description should say when to use the skill ('Use when ...')")
        if len(fm.get("compatibility", "")) > 500:
            errors.append(f"{rel}: compatibility must be <= 500 chars")
        if len(text.splitlines()) > 500:
            errors.append(f"{rel}: SKILL.md over 500 lines; move detail into references/")
        lic = cfg["skills"].get(d.name, {}).get("license")
        if lic == "MIT" and fm.get("license") != "MIT":
            errors.append(f"{rel}: skills.json says MIT, so frontmatter must declare 'license: MIT'")
        if lic == "proprietary" and fm.get("license"):
            errors.append(f"{rel}: proprietary skills must not declare an open-source license")
        if lic not in ("MIT", "proprietary"):
            errors.append(f"{rel}: skills.json license must be 'MIT' or 'proprietary'")
        for ref in sorted(set(re.findall(r"`(references/[^`]+)`", body))):
            if not (d / ref).is_file():
                errors.append(f"{rel}: references missing file {ref} (run scripts/sync_from_kit.py)")
        for f in d.rglob("*"):
            if f.is_symlink():
                errors.append(f"{f.relative_to(ROOT)}: symlinks are not allowed")
            elif f.is_file():
                if f.suffix.lower() not in TEXT_EXT:
                    errors.append(f"{f.relative_to(ROOT)}: only text files ({', '.join(sorted(TEXT_EXT))}) — executables are not allowed in skill packages")
                    continue
                content = f.read_text(encoding="utf-8", errors="replace")
                if f.stat().st_mode & 0o111:
                    errors.append(f"{f.relative_to(ROOT)}: executable bit set")
                if "__CLAUDE_HOME__" in content:
                    errors.append(f"{f.relative_to(ROOT)}: kit placeholder left in skill")
                if SECRET.search(content):
                    errors.append(f"{f.relative_to(ROOT)}: looks like a secret")
        stamp = d / "references" / "KIT_VERSION.txt"
        if stamp.exists():
            stamps.add(stamp.read_text(encoding="utf-8").strip())
    if len(stamps) > 1:
        errors.append(f"skills were synced from different kit versions: {sorted(stamps)}")
    for e in errors:
        print(f"FAIL  {e}")
    print(f"\n{'PASS' if not errors else 'FAIL'}: {len(dirs)} skill(s), {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
