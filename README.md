# claude-secure-agents-skills

**Enterprise security skills for AI coding agents.** Portable [Agent Skills](https://agentskills.io) (`SKILL.md`) that make Claude Code, Cursor, Codex, GitHub Copilot and Gemini CLI review, design and build code against OWASP's LLM, Agentic and application-security standards. Every release is tested against real agent sessions.

| | |
|---|---|
| **Skills** | 6 |
| **Standards** | OWASP Top 10 for LLM Applications 2025 · OWASP Top 10 for Agentic Applications 2026 · OWASP ASVS L2 |
| **Agents** | Claude Code · OpenAI Codex · Cursor · GitHub Copilot (VS Code) · Gemini CLI · any agent that reads `SKILL.md` |
| **Quality gate** | 10 eval cases, 30/30 runs passed on Claude Sonnet ([details](docs/quality.md)) |
| **Footprint** | ~70–85 tokens per skill at session start; 900–1,550 tokens when a skill runs |
| **Integrations** | SARIF 2.1.0 for GitHub code scanning · organization rules via `.security/rules.md` · versioned releases with SHA256SUMS |
| **Owner** | Thakur Dishant Kumar |

---

## Skills

| Skill | Licence | Use it for | Triggers on | Output |
|---|---|---|---|---|
| [`secure-code-review`](skills/secure-code-review/SKILL.md) | MIT | Security and correctness review of a diff, commit or PR | "review my changes", "review before I merge", "is this change safe?" | Verdict APPROVE / REQUEST CHANGES / BLOCK, findings with `file:line`, attack scenario, fix |
| [`ai-security-standard`](skills/ai-security-standard/SKILL.md) | MIT | Applying the security standard while writing code or answering security questions | "is it safe to…", "should we log…", any code touching input, auth, secrets, LLMs, RAG, tools | Rules applied, cited by section |
| [`threat-model`](skills/threat-model/SKILL.md) | Proprietary | Threat modelling a feature, service or AI/agent design | "threat model…", "what could go wrong", design reviews | Assets, data flows, threat table with severity, mitigation and test |
| [`iac-security-review`](skills/iac-security-review/SKILL.md) | Proprietary | Reviewing Terraform, CloudFormation, Kubernetes, Helm, Dockerfiles, compose and GitHub Actions | "review our infrastructure changes", "is this workflow safe?" | Verdict and findings with resource address or `file:line`, exploit scenario, exact setting to change |
| [`dependency-vetting`](skills/dependency-vetting/SKILL.md) | Proprietary | Deciding whether a package, SDK, model API or MCP server is safe | adding, upgrading or pinning a dependency | ADOPT / ADOPT WITH CONDITIONS / REJECT with cited CVEs, licence, maintenance |
| [`secure-feature-build`](skills/secure-feature-build/SKILL.md) | Proprietary | Building a feature end to end under security gates | "build…", "implement…", "add an endpoint / flow / tool" | Sized plan with threat model → approval → verified implementation → review loop → test output |

Licensing and team use: [docs/enterprise.md](docs/enterprise.md).

## For enterprises

| Need | Where |
|---|---|
| Team rollout, version pinning, air-gapped use, licensing | [docs/enterprise.md](docs/enterprise.md) |
| Enforce your company's own security rules | [docs/customization.md](docs/customization.md) |
| Review every PR in CI and publish to GitHub code scanning (SARIF) | [docs/ci-integration.md](docs/ci-integration.md) |
| Verify a release | each GitHub Release has the zips and `SHA256SUMS` (`sha256sum -c SHA256SUMS`) |

## Install

```bash
git clone https://github.com/thakurdishanttt/claude-secure-agents-skills.git
cd claude-secure-agents-skills
python3 scripts/install_skills.py                      # all skills → Claude Code (your user folder)
python3 scripts/install_skills.py --agent cursor --agent codex
python3 scripts/install_skills.py --scope project --project-dir ../my-service   # commit them with a repo
```

Re-run the same command to update; `--list` shows what is installed, `--uninstall` removes only these skills. Then start a new agent session. Per-agent folders and manual steps: [docs/installation.md](docs/installation.md).

## Why it is cheap and fast

- **Progressive loading.** At session start an agent sees only each skill's one-line description. The full `SKILL.md` loads only when the skill is needed, and it reads only the standard sections the change touches (`references/`), never the whole standard.
- **Enforced budgets.** CI fails if a description exceeds 420 characters or a `SKILL.md` exceeds ~1,600 tokens.
- **Sized work.** `secure-feature-build` picks tier S / M / L first, so small changes don't pay for a full planning and review cycle.
- **Measured.** A full eval run takes about 90 s with 10 cases in parallel. A single skill run takes 5–50 s, and most reviews finish in 15–35 s at $0.06–0.10 on Sonnet.

## Accuracy

No AI system is 100% accurate, so this repo measures accuracy instead of claiming it. Before every release, `scripts/run_evals.py` runs each skill in real headless agent sessions against fixtures with planted defects. It checks four things:
- the right skill was chosen, and no skill for unrelated prompts
- the planted vulnerabilities were found
- clean code was not flagged
- read-only skills changed nothing

A release needs **every** run to pass. Results and method: [docs/quality.md](docs/quality.md).

## Security and data handling

- Skills are **text only**: no executables or install scripts, and CI rejects anything else.
- Only `dependency-vetting` uses the web, and it is instructed never to put your code, secrets or internal names into searches.
- Every skill treats repository, web and tool content as **data, not instructions**, which defends against prompt injection.
- The review, threat-model, vetting and IaC skills are read-only. `secure-feature-build` never commits, pushes or deploys unless asked.

Reporting vulnerabilities and the full model: [SECURITY.md](SECURITY.md).

## How it stays current

The security standard has one source of truth: [claude-code-secure-agents](https://github.com/thakurdishanttt/claude-code-secure-agents), which watches Claude Code and OWASP/NIST/MITRE changes and updates itself. A weekly workflow syncs it into every skill's `references/`, bumps the affected skills' versions and opens a pull request. Details: [docs/architecture.md](docs/architecture.md).

## Repository layout

```
skills/
  secure-code-review/         SKILL.md (hand-written) + references/ (generated from the kit — do not edit)
  ai-security-standard/       SKILL.md + references/
  threat-model/               SKILL.md + references/
  dependency-vetting/         SKILL.md + references/
  iac-security-review/        SKILL.md + references/
  secure-feature-build/       SKILL.md + references/
scripts/
  install_skills.py           install / update / list / remove for Claude Code, Codex, Cursor, Copilot, Gemini
  validate_skills.py          Agent Skills format, packaging rules, token budgets
  run_evals.py                eval suite in real headless agent sessions
  extract_sarif.py            pulls and validates SARIF from a review, for CI
  package.py                  reproducible zips + SHA256SUMS (dist/)
  sync_from_kit.py            pulls the security standard from claude-code-secure-agents
evals/
  cases.json                  10 eval cases
  fixtures/                   flask-vuln, util-clean, org-rules, iac-vuln, rag-design, lodash-old, flask-app
  last-run.json               results of the last published run
docs/                         installation, enterprise, customization, ci-integration, architecture, quality
.github/
  workflows/                  ci.yml (validate + package), evals.yml, release.yml (tag → GitHub Release), sync-kit.yml (weekly)
  CODEOWNERS, PULL_REQUEST_TEMPLATE.md, ISSUE_TEMPLATE/
skills.json                   skill list, licence, kit source
```

## Contributing and support

See [CONTRIBUTING.md](CONTRIBUTING.md) for the change process and quality gates, and [CHANGELOG.md](CHANGELOG.md) for releases. Use GitHub issues for bugs and skill requests, and private vulnerability reporting for security issues ([SECURITY.md](SECURITY.md)).

## Licence

Copyright © 2026 Thakur Dishant Kumar. `secure-code-review` and `ai-security-standard` are MIT-licensed; the other skills are proprietary, all rights reserved. See [LICENSE](LICENSE). Licensing questions: thakurdishant1853@gmail.com.
