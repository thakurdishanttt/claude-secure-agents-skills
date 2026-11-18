# CI integration: review every pull request and publish to code scanning

`secure-code-review` and `iac-security-review` can print their findings as SARIF 2.1.0. `scripts/extract_sarif.py` pulls that out of the agent's answer and validates it, and GitHub code scanning (or any SARIF-aware dashboard) then shows each finding on the exact line.

## How it works

1. Claude Code runs headless (`claude -p`) in the checked-out PR, with the skills installed in the repo.
2. The review prints its normal report, plus a SARIF block, because the prompt asks for SARIF.
3. `extract_sarif.py` checks the SARIF (version, rule IDs, levels, file and line for every finding) and writes `review.sarif`.
4. `github/codeql-action/upload-sarif` publishes it to the repository's Security → Code scanning tab and annotates the PR.

Tested end to end: on a branch with planted SQL injection, command injection and path traversal, the pipeline produced a valid SARIF file with all three findings at the correct lines (13, 18, 23).

## Setup

1. Commit the skills into the repository you want reviewed, so CI and developers use the same version:
   ```bash
   python3 /path/to/claude-secure-agents-skills/scripts/install_skills.py --scope project --project-dir . --skill secure-code-review --skill iac-security-review
   git add .claude/skills && git commit -m "Add security review skills"
   ```
2. Copy `scripts/extract_sarif.py` from this repo to `.github/scripts/extract_sarif.py` in that repository.
3. Add an `ANTHROPIC_API_KEY` secret in the repository's settings (Settings → Secrets and variables → Actions).
4. Add this workflow as `.github/workflows/security-review.yml`:

```yaml
name: Security review

on:
  pull_request:

permissions:
  contents: read
  security-events: write   # upload SARIF to code scanning

jobs:
  review:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - run: npm install -g @anthropic-ai/claude-code@2.1.327
      - name: Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          BASE: ${{ github.event.pull_request.base.sha }}
        run: |
          claude -p "Review the changes in this pull request (git diff $BASE...HEAD) and output SARIF." \
            --model sonnet --max-turns 15 --max-budget-usd 1 --output-format json \
            --allowedTools Skill Read Grep Glob "Bash(git diff:*)" "Bash(git log:*)" "Bash(git status:*)" \
            < /dev/null > review.json
          python3 .github/scripts/extract_sarif.py review.json -o review.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: review.sarif
          category: secure-code-review
```

## Notes
- **Forks:** `pull_request` workflows from forks don't receive secrets, so the review runs only on branches in the same repository. Don't switch to `pull_request_target` to work around this: that would run untrusted PR code with your secrets. The `iac-security-review` skill flags exactly that pattern.
- **Tools are read-only:** the allowed tools let the agent read files and git history only. It can't edit, push or call the network.
- **Cost and time:** about $0.06–0.10 and 20–40 s per review on Sonnet for a typical PR, capped by `--max-budget-usd`.
- **Blocking merges:** to fail the job on a BLOCK verdict, add `grep -q '"level": "error"' review.sarif && exit 1` after the extract step, or use code-scanning branch protection rules.
- **Infrastructure PRs:** add a second job, or change the prompt to "review our infrastructure changes … and output SARIF", to run `iac-security-review`.
- Code scanning requires GitHub Advanced Security on private repositories. Public repositories have it for free.
