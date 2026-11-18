# Working in this repository

This repo ships Agent Skills (SKILL.md) that other people install into their
coding agents. Treat every change as a release to customers.

- Never edit `skills/*/references/` — run `python3 scripts/sync_from_kit.py` instead.
- After changing a skill: bump its `metadata.version`, run
  `python3 scripts/validate_skills.py` and `python3 scripts/run_evals.py --repeat 3`
  (costs ~$1.50), and report the eval table. Do not finish with a failing gate.
- Keep descriptions ≤ 420 characters and SKILL.md ≤ ~1,600 tokens.
- Never relax a security rule; never make a read-only skill write.
- Update CHANGELOG.md under "Unreleased".
