# Adding your organization's rules

Every skill reads `.security/rules.md` from the repository it works in, if the file exists. Rules there are **added** to the built-in standard; they can't relax it. This is how a company enforces its own policies (approved libraries, mandatory controls, internal conventions) without forking the skills.

## Format

```markdown
# Organization security rules

These add to the standard. Severity is High unless stated.

- **ORG-1** Every outbound HTTP call MUST set an explicit timeout. Severity: Medium.
- **ORG-2** Secrets MUST be read from the secrets manager client `vault.get()`, never from environment variables. Severity: High.
- **ORG-3** Personal data fields MUST be listed in `docs/data-inventory.md` before they are stored.
```

- Give every rule a stable ID (`ORG-1`, `ORG-2`, …). Findings cite it, so reports and SARIF results can be traced back to your policy.
- A rule is High severity unless it says otherwise. High and Critical findings block the change.
- Write rules as testable statements ("MUST set a timeout"), not intentions ("be careful with HTTP").
- Keep the file short. It is read on every run, so ~20 rules costs about 500 tokens.

## Rolling it out
- **One repository:** commit `.security/rules.md` at the repository root.
- **Many repositories:** keep the file in a central policy repo and sync it into each repository, for example with a template repository, a scheduled workflow, or your existing config-management tooling. Every repo then enforces the same rule IDs.
- **Project conventions** that aren't security rules belong in `AGENTS.md` or `CLAUDE.md`, which the skills also respect.

## Verified behaviour
The eval case `review-enforces-org-rules` uses the example above. A change that adds an HTTP call without a timeout, and is otherwise clean, must be reported as `ORG-1` with a REQUEST CHANGES verdict. It passed 3 out of 3 runs.
