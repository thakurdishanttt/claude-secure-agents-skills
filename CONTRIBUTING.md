# Contributing

Thanks for helping. These skills run inside other people's agents, often on
enterprise code, so every change goes through the same gates.

## Ground rules
- **Never edit `skills/*/references/`.** It is generated from the
  [kit's standard](https://github.com/thakurdishanttt/claude-code-secure-agents/blob/main/standards/ai-security.md).
  Propose rule changes there; they arrive here through the weekly sync.
- Security rules may be **added or tightened, never relaxed**.
- Keep skills **agent-neutral**: no instructions that only work in one agent, unless they have a fallback.
- **Read-only skills stay read-only.** Nothing commits, pushes or deploys unless the user asks.
- Stay within the **token budgets**: description ≤ 420 characters, `SKILL.md` ≤ ~1,600 tokens. Move detail into references, not into SKILL.md.

## Making a change
1. Branch from `main`.
2. Edit the skill's `SKILL.md` (e.g. `skills/threat-model/SKILL.md`) and bump its `metadata.version` (patch: wording; minor: new behaviour; major: changed output format).
3. Run the gates:
   ```bash
   python3 scripts/validate_skills.py                 # must pass
   python3 scripts/run_evals.py --repeat 3            # must be 100% for skill or eval changes (~$1.50)
   python3 scripts/package.py                         # zips build
   ```
4. Update `CHANGELOG.md` under **Unreleased**.
5. Open a PR using the template and paste the eval table. CODEOWNERS review is required.

## Adding a skill
- Folder name = `name` in frontmatter (lowercase, hyphens, ≤ 64 characters).
- Description says **what** it does and **when** to use it, with two or three example phrases users actually type.
- Add it to `skills.json` with its licence, and add at least one eval case. For a review-type skill, add both a should-find and a should-not-flag case.
- MIT skills declare `license: MIT` in frontmatter; proprietary skills declare no licence field.

## Reporting bugs
- Wrong or missed finding → open an issue with a minimal code example; it becomes an eval case.
- Security issue → follow [SECURITY.md](SECURITY.md) instead of opening an issue.

## Commit and PR style
Short imperative subject ("Tighten SSRF guidance in review skill"), with a body saying why. One logical change per PR.
