#!/usr/bin/env python3
"""Run the skill eval suite against real Claude Code sessions.

  python3 scripts/run_evals.py                     # all cases, Sonnet, 4 in parallel
  python3 scripts/run_evals.py --case review-finds-planted-vulns --repeat 3
  python3 scripts/run_evals.py --model opus --jobs 7 --json evals/last-run.json

For each case: copy the fixture to a temp folder, commit `base/`, apply
`change/` as the working-tree diff, install ALL skills into `.claude/skills/`
(so skill *selection* is tested, not just the skill), then run
`claude -p` headless and check:
  * the expected skill was invoked (or no skill, for negative cases)
  * every `must` pattern appears in the final answer, no `must_not` does
  * the working tree is unchanged when `unchanged` is set (read-only skills)
  * time, turns and cost per case

Prints a Markdown table and exits non-zero unless every run passes.
Costs real API usage (roughly $0.05–0.50 per case on Sonnet). Stdlib only.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout


def prepare(case: dict, work: Path) -> None:
    fx = EVALS / "fixtures" / case["fixture"]
    shutil.copytree(fx / "base", work, dirs_exist_ok=True)
    git(work, "init", "-q", "-b", "main")
    git(work, "-c", "user.name=eval", "-c", "user.email=eval@example.invalid", "add", "-A")
    git(work, "-c", "user.name=eval", "-c", "user.email=eval@example.invalid", "commit", "-qm", "base")
    if (fx / "change").is_dir():
        shutil.copytree(fx / "change", work, dirs_exist_ok=True)
        git(work, "add", "-N", ".")          # make new files visible to `git diff`
    shutil.copytree(ROOT / "skills", work / ".claude" / "skills")


def run_case(case: dict, model: str, budget: float) -> dict:
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f"eval-{case['id']}-") as d:
        work = Path(d)
        prepare(case, work)
        before = git(work, "status", "--porcelain", "--untracked-files=all", "--", ".", ":!.claude")
        tools = ["Skill", *case["tools"]]
        cmd = [
            "claude", "-p", case["prompt"],
            "--model", model,
            "--max-turns", str(case.get("max_turns", 15)),
            "--max-budget-usd", str(budget),
            "--output-format", "stream-json", "--verbose",
            "--setting-sources", "project",       # ignore the runner's own user settings/skills
            "--allowedTools", *tools,
        ]
        env = {**os.environ, "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
        try:
            proc = subprocess.run(cmd, cwd=work, capture_output=True, text=True,
                                  timeout=case.get("timeout_s", 420), stdin=subprocess.DEVNULL, env=env)
            out = proc.stdout
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        skills_used: list[str] = []
        result_text, cost, turns, is_error = "", 0.0, 0, False
        for line in out.splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("type") == "assistant":
                for block in ev.get("message", {}).get("content", []) or []:
                    if block.get("type") == "tool_use" and block.get("name") == "Skill":
                        skills_used.append(str((block.get("input") or {}).get("skill", "")).split(":")[-1])
            elif ev.get("type") == "result":
                result_text = ev.get("result") or ""
                cost = float(ev.get("total_cost_usd") or 0)
                turns = int(ev.get("num_turns") or 0)
                is_error = bool(ev.get("is_error"))
        after = git(work, "status", "--porcelain", "--untracked-files=all", "--", ".", ":!.claude")

    fails: list[str] = []
    want = case["skill"]
    if want and want not in skills_used:
        fails.append(f"skill '{want}' not used (used: {skills_used or 'none'})")
    if not want and skills_used:
        fails.append(f"no skill expected, used {skills_used}")
    if not result_text:
        fails.append("no final answer (timeout, turn or budget limit)" + (" [error]" if is_error else ""))
    for pat in case.get("must", []):
        if not re.search(pat, result_text, re.I | re.M):
            fails.append(f"missing /{pat}/")
    for pat in case.get("must_not", []):
        if re.search(pat, result_text, re.I | re.M):
            fails.append(f"forbidden /{pat}/ present")
    if case.get("unchanged") and before != after:
        fails.append("working tree was modified")
    if "sarif_min_results" in case:
        sys.path.insert(0, str(ROOT / "scripts"))
        import extract_sarif  # noqa: E402
        try:
            log = extract_sarif.extract(result_text)
            errs = extract_sarif.problems(log)
            n = sum(len(r.get("results", [])) for r in log["runs"])
            if errs:
                fails.append("invalid SARIF: " + "; ".join(errs[:3]))
            if n < case["sarif_min_results"]:
                fails.append(f"SARIF has {n} result(s), expected >= {case['sarif_min_results']}")
        except ValueError as exc:
            fails.append(str(exc))
    return {"id": case["id"], "pass": not fails, "fails": fails, "skills": skills_used,
            "seconds": round(time.monotonic() - t0, 1), "turns": turns, "cost_usd": round(cost, 4),
            "answer_excerpt": result_text[:600]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", action="append", help="run only these case ids")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--jobs", type=int, default=4, help="cases run in parallel")
    ap.add_argument("--repeat", type=int, default=1, help="runs per case (consistency check)")
    ap.add_argument("--budget", type=float, default=1.0, help="max USD per run")
    ap.add_argument("--json", help="write full results here")
    a = ap.parse_args()
    if not shutil.which("claude"):
        print("claude CLI not found; install Claude Code first", file=sys.stderr)
        return 2
    cases = json.loads((EVALS / "cases.json").read_text(encoding="utf-8"))["cases"]
    if a.case:
        cases = [c for c in cases if c["id"] in set(a.case)]
    runs = [c for c in cases for _ in range(a.repeat)]
    t0 = time.monotonic()
    with cf.ThreadPoolExecutor(max_workers=a.jobs) as pool:
        results = list(pool.map(lambda c: run_case(c, a.model, a.budget), runs))
    wall = time.monotonic() - t0

    passed = sum(r["pass"] for r in results)
    print(f"| Case | Result | Skill used | Time (s) | Turns | Cost ($) |\n|---|---|---|---|---|---|")
    for r in results:
        print(f"| {r['id']} | {'PASS' if r['pass'] else 'FAIL'} | {', '.join(r['skills']) or '—'} | "
              f"{r['seconds']} | {r['turns']} | {r['cost_usd']:.3f} |")
    total = sum(r["cost_usd"] for r in results)
    print(f"\n**{passed}/{len(results)} passed** · model {a.model} · wall time {wall:.0f}s "
          f"({a.jobs} parallel) · total cost ${total:.2f}")
    for r in results:
        if not r["pass"]:
            print(f"\nFAIL {r['id']}:\n  - " + "\n  - ".join(r["fails"]) + f"\n  answer: {r['answer_excerpt'][:300]!r}")
    if a.json:
        Path(a.json).write_text(json.dumps({"model": a.model, "results": results}, indent=2) + "\n", encoding="utf-8")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
