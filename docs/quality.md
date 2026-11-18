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
| `iac-review-finds-misconfigs` | Picks `iac-security-review` and finds the planted Terraform, Kubernetes, Docker and GitHub Actions issues: open SSH, wildcard IAM, public database, privileged container, root image, `pull_request_target`, unpinned action. Verdict BLOCK. |
| `threat-model-rag-design` | Picks `threat-model`. Covers prompt injection, tenant isolation, the auto-executing refund tool (excessive agency) and the missing rate limit, in a threat table. |
| `dependency-vetting-known-cve` | Picks `dependency-vetting` for lodash 4.17.15. Cites a known CVE, recommends upgrading to 4.17.21, and verdict is REJECT or ADOPT WITH CONDITIONS. |
| `feature-build-plans-and-waits` | Picks `secure-feature-build`. States a tier, writes a threat model and **waits for approval**, writing no code before you agree. |
| `standard-answers-logging-question` | Picks `ai-security-standard`. Says not to log full prompts unredacted and names the PII or secret risk. |
| `no-skill-for-unrelated-task` | Uses **no** skill for an unrelated prompt (false-trigger check). |

Cases live in [`evals/cases.json`](../evals/cases.json) and fixtures in [`evals/fixtures/`](../evals/fixtures/).

## Latest results

Claude Sonnet, 3 runs per case, 10 cases in parallel, 2026-11-18:

| Case | Pass | Avg time | Avg cost |
|---|---|---|---|
| review-finds-planted-vulns | 3/3 | 23 s | $0.068 |
| review-no-false-positive | 3/3 | 35 s | $0.080 |
| review-sarif-output | 3/3 | 36 s | $0.088 |
| review-enforces-org-rules | 3/3 | 22 s | $0.070 |
| iac-review-finds-misconfigs | 3/3 | 33 s | $0.094 |
| threat-model-rag-design | 3/3 | 42 s | $0.103 |
| dependency-vetting-known-cve | 3/3 | 34 s | $0.108 |
| feature-build-plans-and-waits | 3/3 | 27 s | $0.087 |
| standard-answers-logging-question | 3/3 | 15 s | $0.059 |
| no-skill-for-unrelated-task | 3/3 | 5 s | $0.030 |
| **Total** | **30/30** | 92 s wall | $2.36 |

Raw results: [`evals/last-run.json`](../evals/last-run.json).

**What the suite caught during development:** shortened descriptions (~250 characters) made the review and standard skills stop triggering on "review my changes" when all five were installed. On first run, 3 of 7 cases failed. Restoring explicit trigger phrases fixed it, and the 420-character budget reflects that measurement.

## Running it

```bash
python3 scripts/run_evals.py --jobs 10                         # all cases once (~$0.80, ~50 s)
python3 scripts/run_evals.py --repeat 3 --jobs 10              # consistency check (~$2.40, ~90 s)
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
- Cases run on Claude Code. Other agents use the same `SKILL.md`, but their skill selection isn't covered by CI yet.
- `dependency-vetting` depends on live web results and may vary as advisories change.
