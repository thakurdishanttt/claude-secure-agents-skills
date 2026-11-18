# Changelog

All notable changes to the skills. Each skill also carries its own version in
`metadata.version`.

## Unreleased
### Added
- `iac-security-review` 1.0.0: reviews Terraform, CloudFormation, Kubernetes, Helm, Dockerfiles, compose and GitHub Actions.
- Organization rules: every skill reads `.security/rules.md` and enforces it by rule ID (all skills 1.2.0).
- SARIF 2.1.0 output from `secure-code-review` and `iac-security-review` when asked; `scripts/extract_sarif.py` validates it; GitHub code-scanning recipe in `docs/ci-integration.md` (tested end to end).
- Reproducible zips with `SHA256SUMS`; `release.yml` publishes a GitHub Release when a date tag is pushed.
- `docs/enterprise.md` (rollout, pinning, air-gapped use, data handling, licensing, contact) and `docs/customization.md`.
- Three eval cases (SARIF, org rules, IaC). Full suite: 30/30 runs passed on Sonnet.
### Changed
- Removed placeholder text from docs and templates.
- `secure-code-review` 1.1.1 and `secure-feature-build` 1.1.1: concrete examples instead of placeholders.

## 2026-11-18
### Added
- Five skills: `secure-code-review` and `ai-security-standard` (MIT); `threat-model`, `dependency-vetting` and `secure-feature-build`. All v1.1.0.
- Eval suite (`scripts/run_evals.py`, 7 cases with fixtures). First published run: 21/21 passed on Claude Sonnet.
- Installer for Claude Code, Codex, Cursor, GitHub Copilot and Gemini CLI (`scripts/install_skills.py`).
- Validator with Agent Skills format, packaging rules and token budgets. Packager for skill zips.
- Weekly sync of the security standard from claude-code-secure-agents.
- Enterprise documentation: installation, architecture, quality, security policy, contributing guide.

### Changed
- Shorter reference file names and a compact section index (about 10% fewer tokens per skill run).
- Descriptions rewritten with explicit trigger phrases. Measured: shorter descriptions missed triggers when all skills were installed.
