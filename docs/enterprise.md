# Enterprise guide

## What you get
- **Six security skills** for AI coding agents: `secure-code-review`, `ai-security-standard`, `threat-model`, `dependency-vetting`, `iac-security-review` and `secure-feature-build`.
- **One standard** behind all of them: OWASP Top 10 for LLM Applications 2025, OWASP Top 10 for Agentic Applications 2026, and OWASP ASVS L2. It is kept current from [claude-code-secure-agents](https://github.com/thakurdishanttt/claude-code-secure-agents).
- **Your own rules** enforced alongside it, through `.security/rules.md` ([customization.md](customization.md)).
- **SARIF output** for GitHub code scanning and security dashboards ([ci-integration.md](ci-integration.md)).
- **Measured quality:** every release passes the full eval suite ([quality.md](quality.md)).
- **Audit support:** a control mapping for SOC 2, ISO/IEC 27001:2022, PCI DSS v4.0 and NIST SSDF ([compliance.md](compliance.md)).

## Rolling out to a team
1. **Pick a version.** Each GitHub Release (tagged by date, for example `v2026.11.18`) contains one zip per skill and `SHA256SUMS`. Verify downloads with `sha256sum -c SHA256SUMS`. The zips are reproducible, so rebuilding a tag gives identical hashes.
2. **Install per repository** so everyone, including CI, uses the same version:
   `python3 scripts/install_skills.py --scope project --project-dir ../payments-api` (your repository's path), then commit the agent's skills folder (for Claude Code, `.claude/skills/`).
   Or install per developer with `--scope user`. The supported agents are Claude Code, Codex, Cursor, GitHub Copilot and Gemini CLI ([installation.md](installation.md)).
3. **Add your policy** in `.security/rules.md`.
4. **Gate pull requests** with the CI workflow in [ci-integration.md](ci-integration.md).
5. **Update** by moving to a newer release tag. [CHANGELOG.md](../CHANGELOG.md) lists every change, and each skill's own version is in its `SKILL.md`.

## Data handling and security
- The skills are plain text. They contain no executables, install scripts or telemetry, and CI rejects anything else.
- The skills themselves send nothing anywhere. Your agent sends prompts and code to its model provider under your existing agreement with that provider.
- Only `dependency-vetting` uses the web, to check public advisories and package registries. It is instructed never to put code, secrets, internal hostnames or customer names into searches.
- **Air-gapped or restricted environments:** every skill except `dependency-vetting` works without network access.
- The review, threat-model, vetting and IaC skills are read-only. `secure-feature-build` asks you to approve its plan first, and never commits, pushes or deploys unless asked.
- Every skill treats repository, web and tool content as data, never as instructions (prompt-injection defence).
- Vulnerability reporting and response targets: [SECURITY.md](../SECURITY.md).

## What is tested, and what isn't
- **Tested in CI:** Claude Code with Claude Sonnet; Opus and Haiku are run before each release. The cases cover skill selection, planted-vulnerability detection (including a cross-file IDOR), false positives on safe-but-scary code, organization rules, SARIF validity and read-only behaviour ([quality.md](quality.md)).
- **Supported but not yet in CI:** the other agents. They load the same `SKILL.md` files, but their skill selection is not yet covered by automated tests. Please report differences as issues.
- **Limits:** these skills make an agent apply a security standard consistently. They don't replace penetration testing, SAST/DAST tools or a human security review for high-risk releases.

## Licensing
- `secure-code-review` and `ai-security-standard` are MIT-licensed.
- The other skills are proprietary (see [LICENSE](../LICENSE)). Team and organization licences, including deployment through your own repositories or CI and support, are available on request.

## Contact
- Licensing and support: **thakurdishant1853@gmail.com**
- Bugs and feature requests: [GitHub issues](https://github.com/thakurdishanttt/claude-secure-agents-skills/issues)
- Security vulnerabilities: [private vulnerability reporting](https://github.com/thakurdishanttt/claude-secure-agents-skills/security/advisories/new) (see [SECURITY.md](../SECURITY.md))
