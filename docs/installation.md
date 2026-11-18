# Installation

## Requirements
- Python 3.9+ (only for the installer script; the skills themselves are plain Markdown)
- One or more supported agents

## With the installer (recommended)

```bash
python3 scripts/install_skills.py [--agent AGENT]... [--scope user|project] [--project-dir DIR] [--skill NAME]...
```

| Option | Default | Meaning |
|---|---|---|
| `--agent` | `claude` | `claude`, `codex`, `cursor`, `copilot`, `gemini`; repeat for several |
| `--scope` | `user` | `user` = all your projects; `project` = one repo (commit the folder so the team gets it) |
| `--project-dir` | `.` | project root for `--scope project` |
| `--skill` | all | install only the named skills |
| `--list` | | show installed versions and whether an update is available |
| `--uninstall` | | remove these skills (other skills are never touched) |

Updating: `git pull`, then re-run the same command. Each skill folder is written fully before it replaces the old one.

## Where each agent looks

Each skill is its own folder inside these, for example `~/.claude/skills/secure-code-review/`.

| Agent | User folder | Project folder |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| OpenAI Codex | `~/.agents/skills/` | `.agents/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` (also reads `.agents/skills/`) |
| GitHub Copilot (VS Code) | `~/.copilot/skills/` | `.github/skills/` (VS Code also reads `.claude/skills/` and `.agents/skills/`) |
| Gemini CLI | `~/.gemini/skills/` | `.gemini/skills/` (falls back to `.agents/skills/`) |

To install by hand, copy each skill folder you want — for example `skills/secure-code-review/`, including its `references/` folder — into one of these. Start a new session afterwards.

Agent support for skills is evolving; if a path changes, check the agent's own documentation and open an issue so we can update `scripts/install_skills.py`.

## Teams and enterprises
- **Project scope** is the simplest way to roll out to a team: run the installer with `--scope project`, commit the folder, and everyone who clones the repo gets the same skill versions.
- Pin a release: check out a tag of this repo before installing.
- For the full Claude Code multi-agent kit with global rules and fleet auto-update, use [claude-code-secure-agents](https://github.com/thakurdishanttt/claude-code-secure-agents).

## Verify
Ask your agent to "review my changes" in a repo with an uncommitted change. It should announce the `secure-code-review` skill and end with a verdict.
