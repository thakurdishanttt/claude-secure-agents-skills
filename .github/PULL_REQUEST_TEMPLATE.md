## What and why
Describe the change and the reason in one or two sentences.

## Skills changed
List each changed skill with its version change, e.g. `threat-model 1.1.0 → 1.2.0`.

## Gates
- [ ] `python3 scripts/validate_skills.py` passes
- [ ] `python3 scripts/run_evals.py --repeat 3` is 100% (required when skills/ or evals/ change) — paste the table below
- [ ] `metadata.version` bumped for each changed skill
- [ ] CHANGELOG.md updated under Unreleased
- [ ] No security rule relaxed; read-only skills still read-only; no edits in `references/`

## Eval results
Paste the table printed by `python3 scripts/run_evals.py --repeat 3`.
