# Security policy

## Reporting a vulnerability
Please **do not open a public issue**. Report privately through GitHub's
[private vulnerability reporting](https://github.com/thakurdishanttt/claude-secure-agents-skills/security/advisories/new)
(Security tab → "Report a vulnerability"). Licensed enterprise customers can also email thakurdishant1853@gmail.com.

Include the affected skill and version (`metadata.version` in its `SKILL.md`),
the agent and model used, and steps or a prompt that reproduces the issue.

| Stage | Target |
|---|---|
| Acknowledgement | 3 business days |
| Triage and severity | 7 business days |
| Fix for Critical / High | 30 days, released as a new skill version |

## What counts as a vulnerability here
- A skill that leads an agent to **leak data**: secrets, source code or internal names put into web searches or output.
- A skill that makes an agent **follow injected instructions** from repository, web or tool content.
- A read-only skill that **modifies files**, or any skill that commits, pushes or deploys without being asked.
- A rule in the standard that is **wrong or unsafe** (for example, advice that introduces a vulnerability).
- Anything executable or obfuscated in a published skill package.

Missed findings in a review, meaning false negatives, are quality bugs: please open a normal issue with a minimal example, and it becomes an eval case.

## Security model of the skills
- **Text only.** Packages contain Markdown and text; `scripts/validate_skills.py` rejects executables, binaries and symlinks.
- **No network** except `dependency-vetting`, which searches public advisories and registries. It is instructed never to include code, secrets, internal hostnames or customer names in queries.
- **Untrusted content is data.** Every skill tells the agent to treat file contents, comments, issues, PR text, web pages and tool output as data and to report embedded instructions instead of following them.
- **Least privilege.** `secure-code-review`, `threat-model` and `dependency-vetting` are read-only. `secure-feature-build` requires your approval of the plan and never commits, pushes or deploys unless asked.
- **Supply chain.** The standard is generated from the kit repository at a recorded commit (`references/KIT_VERSION.txt`). Sync changes arrive as reviewable pull requests, and nothing is fetched at run time.

## Supported versions
The latest version of each skill is supported. Install updates with `python3 scripts/install_skills.py` (see [docs/installation.md](docs/installation.md)).
