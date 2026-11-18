#!/usr/bin/env python3
"""Install, update or remove these skills for one or more coding agents.

  python3 scripts/install_skills.py                          # all skills → Claude Code, your user folder
  python3 scripts/install_skills.py --agent cursor --agent codex
  python3 scripts/install_skills.py --scope project --project-dir ../my-service
  python3 scripts/install_skills.py --skill secure-code-review --skill threat-model
  python3 scripts/install_skills.py --uninstall
  python3 scripts/install_skills.py --list                   # show what is installed where

Re-running updates skills in place (a skill folder is replaced only after the
new copy is fully written). Only folders this repo ships are ever touched.
Stdlib only; works on macOS, Linux and Windows.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
# (user folder, project folder) per agent. Sources: each agent's docs on Agent Skills.
TARGETS = {
    "claude":  (HOME / ".claude" / "skills",  Path(".claude") / "skills"),
    "codex":   (HOME / ".agents" / "skills",  Path(".agents") / "skills"),
    "cursor":  (HOME / ".cursor" / "skills",  Path(".cursor") / "skills"),
    "copilot": (HOME / ".copilot" / "skills", Path(".github") / "skills"),
    "gemini":  (HOME / ".gemini" / "skills",  Path(".gemini") / "skills"),
}


def shipped() -> dict[str, str]:
    out = {}
    for d in sorted((ROOT / "skills").iterdir()):
        f = d / "SKILL.md"
        if f.is_file():
            m = re.search(r'^\s+version:\s*"?([0-9.]+)"?', f.read_text(encoding="utf-8"), re.M)
            out[d.name] = m.group(1) if m else "?"
    return out


def installed_version(folder: Path) -> str | None:
    f = folder / "SKILL.md"
    if not f.is_file():
        return None
    m = re.search(r'^\s+version:\s*"?([0-9.]+)"?', f.read_text(encoding="utf-8", errors="replace"), re.M)
    return m.group(1) if m else "?"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", action="append", choices=sorted(TARGETS), help="default: claude")
    ap.add_argument("--scope", choices=["user", "project"], default="user")
    ap.add_argument("--project-dir", default=".", help="project root for --scope project")
    ap.add_argument("--skill", action="append", help="default: all skills in this repo")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    skills = shipped()
    chosen = a.skill or list(skills)
    unknown = sorted(set(chosen) - set(skills))
    if unknown:
        print(f"unknown skill(s): {', '.join(unknown)}; available: {', '.join(skills)}", file=sys.stderr)
        return 2
    agents = a.agent or ["claude"]

    for agent in agents:
        user_dir, proj_rel = TARGETS[agent]
        base = user_dir if a.scope == "user" else Path(a.project_dir).resolve() / proj_rel
        if a.list:
            for name in skills:
                v = installed_version(base / name)
                print(f"{agent:8} {base / name}: {'not installed' if v is None else 'v' + v}"
                      f"{'' if v in (None, skills[name]) else f'  (repo has v{skills[name]})'}")
            continue
        for name in chosen:
            dest = base / name
            if a.uninstall:
                if dest.is_dir():
                    shutil.rmtree(dest)
                    print(f"removed   {agent:8} {name}")
                continue
            base.mkdir(parents=True, exist_ok=True)
            old = installed_version(dest)
            # Copy to a temp folder next to the target, then swap, so a failure never leaves half a skill.
            tmp = Path(tempfile.mkdtemp(prefix=f".{name}-", dir=base))
            try:
                shutil.copytree(ROOT / "skills" / name, tmp / name)
                if dest.exists():
                    shutil.rmtree(dest)
                (tmp / name).rename(dest)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            action = "installed" if old is None else ("updated  " if old != skills[name] else "refreshed")
            print(f"{action} {agent:8} {name} v{skills[name]} → {dest}")
    if not a.list and not a.uninstall:
        print("\nStart a new agent session to load the skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
