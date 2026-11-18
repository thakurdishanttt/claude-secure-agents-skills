#!/usr/bin/env python3
"""Zip each skill for distribution (one installable folder per zip).

  python3 scripts/package.py            # one zip per skill, e.g. dist/threat-model-1.1.0.zip
  python3 scripts/package.py --pack     # plus all skills in one zip, e.g. dist/claude-secure-agents-skills-pack-2026-11-18.zip

Each zip holds one folder named after the skill with SKILL.md inside, which is
what agents and skill installers expect. No nested zips. Zips are reproducible
(fixed timestamps and permissions), and dist/SHA256SUMS lists their hashes so
users and release pipelines can verify them (`sha256sum -c SHA256SUMS`).
Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def version_of(skill: Path) -> str:
    m = re.search(r'^\s+version:\s*"?([0-9][^"\s]*)"?', (skill / "SKILL.md").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else "0.0.0"


def add_tree(z: zipfile.ZipFile, skill: Path, prefix: str) -> None:
    for f in sorted(skill.rglob("*")):
        if f.is_file() and not f.is_symlink():
            info = zipfile.ZipInfo(f"{prefix}{f.relative_to(skill.parent).as_posix()}", date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, f.read_bytes())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", action="store_true")
    a = ap.parse_args()
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for old in dist.glob("*.zip"):
        old.unlink()
    skills = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
    for s in skills:
        out = dist / f"{s.name}-{version_of(s)}.zip"
        with zipfile.ZipFile(out, "w") as z:
            add_tree(z, s, "")
        print(f"{out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB")
    if a.pack:
        out = dist / f"claude-secure-agents-skills-pack-{dt.date.today().isoformat()}.zip"
        with zipfile.ZipFile(out, "w") as z:
            for s in skills:
                add_tree(z, s, "")
        print(f"{out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB")
    sums = "".join(f"{hashlib.sha256(z.read_bytes()).hexdigest()}  {z.name}\n" for z in sorted(dist.glob("*.zip")))
    (dist / "SHA256SUMS").write_text(sums, encoding="utf-8")
    print("dist/SHA256SUMS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
