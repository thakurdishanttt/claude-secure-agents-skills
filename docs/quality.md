# Quality: how accuracy, speed and cost are measured

## Policy
- **No release without a green eval run.** Every case must pass on every run; there is no "mostly passing".
- **Measure, don't claim.** AI agents are not deterministic and no skill is 100% accurate. Accuracy is the pass rate across repeated runs, published below.
- **Budgets are enforced in CI:** description ≤ 420 characters and `SKILL.md` ≤ ~1,600 tokens per skill.

## What is tested

Each case runs `claude -p` headless in a temporary copy of a fixture repo. All six skills are installed, so the agent has to **choose** the right one.

| Case | Checks |
|---|---|
| `review-finds-planted-vulns` | Picks `secure-code-review`. Finds the planted SQL injection, command injection and path traversal. Verdict BLOCK. No files changed. |
| `review-no-false-positive` | Picks `secure-code-review` on a clean, tested change. Verdict APPROVE with no Critical or High finding, so no crying wolf. |
| `review-sarif-output` | When asked for SARIF, returns a valid SARIF 2.1.0 log (checked by `extract_sarif.py`) with at least 3 located findings. |
| `review-enforces-org-rules` | Reads `.security/rules.md` and reports the violated company rule by its ID (`ORG-1`) with a REQUEST CHANGES or BLOCK verdict. |
| `review-multi-file-idor` | Finds a missing tenant check that only shows up by reading across four files (routes → service → repository → auth). Names the IDOR and the files. Verdict REQUEST CHANGES or BLOCK. |
| `review-safe-but-scary-no-false-alarm` | Approves code that *looks* dangerous but is safe: `subprocess` with fixed arguments, a checksum-verified download, an allowlisted `ORDER BY`. No Critical or High finding. |
| `iac-review-finds-misconfigs` | Picks `iac-security-review` and finds the planted Terraform, Kubernetes, Docker and GitHub Actions issues: open SSH, wildcard IAM, public database, privileged container, root image, `pull_request_target`, unpinned action. Verdict BLOCK. |
| `threat-model-rag-design` | Picks `threat-model`. Covers prompt injection, tenant isolation, the auto-executing refund tool (excessive agency) and the missing rate limit, in a threat table. |
| `dependency-vetting-known-cve` | Picks `dependency-vetting` for lodash 4.17.15. Cites a known CVE, recommends upgrading to 4.17.21, and verdict is REJECT or ADOPT WITH CONDITIONS. |
| `feature-build-plans-and-waits` | Picks `secure-feature-build` on a small accounts app. States a tier, writes a threat model and **waits for approval**, writing no code before you agree. |
| `standard-answers-logging-question` | Picks `ai-security-standard`. Says not to log full prompts unredacted and names the PII or secret risk. |
| `no-skill-for-unrelated-task` | Uses **no** skill for an unrelated prompt (false-trigger check). |

Cases live in [`evals/cases.json`](../evals/cases.json) and fixtures in [`evals/fixtures/`](../evals/fixtures/).

## Latest results

Claude Sonnet, 3 runs per case, 12 cases in parallel, 2026-11-18:

| Case | Pass | Avg time | Avg cost |
|---|---|---|---|
| review-finds-planted-vulns | 3/3 | 44 s | $0.070 |
| review-no-false-positive | 3/3 | 41 s | $0.068 |
| review-sarif-output | 3/3 | 50 s | $0.088 |
| review-enforces-org-rules | 3/3 | 44 s | $0.075 |
| review-multi-file-idor | 3/3 | 21 s | $0.072 |
| review-safe-but-scary-no-false-alarm | 3/3 | 27 s | $0.079 |
| iac-review-finds-misconfigs | 3/3 | 33 s | $0.092 |
| threat-model-rag-design | 3/3 | 33 s | $0.095 |
| dependency-vetting-known-cve | 3/3 | 26 s | $0.096 |
| feature-build-plans-and-waits | 3/3 | 24 s | $0.095 |
| standard-answers-logging-question | 3/3 | 13 s | $0.058 |
| no-skill-for-unrelated-task | 3/3 | 4 s | $0.030 |
| **Total** | **36/36** | 99 s wall | $2.75 |

Same suite on other models, one run per case, same day:

| Model | Pass | Wall time | Cost |
|---|---|---|---|
| Claude Sonnet (×3) | 36/36 | 99 s | $2.75 |
| Claude Opus | 12/12 | 80 s | $2.16 |
| Claude Haiku | 12/12 | 64 s | $0.09 (as reported by the CLI) |

Raw results, including each full answer: [`evals/last-run.json`](../evals/last-run.json), [`last-run-opus.json`](../evals/last-run-opus.json), [`last-run-haiku.json`](../evals/last-run-haiku.json).

**What the suite caught during development:**
- Shortened descriptions (~250 characters) made the review and standard skills stop triggering on "review my changes" when all skills were installed. Restoring explicit trigger phrases fixed it; the 420-character budget reflects that measurement.
- Haiku skipped `secure-feature-build` and started writing code straight away. The description now says to load it before writing any code (1.2.1), and Haiku then passed 6/6 repeats.
- Haiku found a real bug in the first draft of the "safe" fixture (version strings sorted as text). The fixture was fixed; a false-positive test must be genuinely clean.
- A test run left `__pycache__` in a fixture, and reviewers correctly flagged it. Fixtures are now copied without build junk.
- Several failures were grader regexes that were too strict for correct answers (for example "allows everything" for a wildcard IAM policy). Each was checked against the full answer before the pattern was widened.

## Running it

```bash
python3 scripts/run_evals.py --jobs 12                         # all cases once (~$0.95, ~60 s)
python3 scripts/run_evals.py --repeat 3 --jobs 12              # consistency check (~$2.75, ~100 s)
python3 scripts/run_evals.py --case threat-model-rag-design --model opus
python3 scripts/run_evals.py --json evals/last-run.json        # save results
```

Needs the Claude Code CLI, signed in or with `ANTHROPIC_API_KEY` set. Each run has a per-case spending cap (`--budget`, default $1).

## Adding a case
1. Add a fixture folder under `evals/fixtures/` (see `evals/fixtures/flask-vuln/` for the pattern): `base/` is committed first, and `change/` holds the edited files when the case reviews a diff.
2. Add the case to `evals/cases.json`: the expected `skill` (or `null`), the `prompt`, allowed `tools`, `must` and `must_not` regexes, and `unchanged` for read-only skills.
3. Run it with `--repeat 3`. A case that passes only sometimes is a finding: fix the skill, not the test.
4. Every bug reported against a skill should become a case.

## Limits of this suite
- Regex checks confirm that findings are *present*; they don't grade the quality of every sentence. Spot-read the excerpts in the JSON after changes.
- Cases run on Claude Code (Sonnet in CI; Opus and Haiku before each release). Other agents use the same `SKILL.md`, but their skill selection isn't covered by CI yet.
- `dependency-vetting` depends on live web results and may vary as advisories change.
