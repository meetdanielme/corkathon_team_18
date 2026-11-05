# Shared team skills

Selected from [Matt Pocock's skills](https://github.com/mattpocock/skills), under the included MIT [licence](LICENSE). These are committed snapshots, copied unchanged from the versions installed on 5 November 2026; no automatic updates.

- `grill-me` — interview entry point; uses `grilling`.
- `grilling` — supporting interview instructions.
- `to-tickets` — turn the agreed MVP into GitHub issues, following `docs/agents/issue-tracker.md`.
- `handoff` — prepare context for another agent/session.

Codex discovers `.agents/skills/`. Claude Code uses the relative `.claude/skills` symlink to this directory. Clone with symlink support (standard on macOS/Linux), then start a new agent session. No separate global install is needed.

If a host has no Skill tool, ask it to read the relevant `SKILL.md` directly. For `grill-me`, also read `grilling/SKILL.md`.

Only this shared directory is tracked under `.agents/`; private `.agents/AGENTS.md` remains ignored. The parent project's event rules still apply: skills are tool setup, not permission to implement before the event.
