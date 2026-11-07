# Team memory

Last updated: 7 November 2026. Shared project context, not a chat transcript.

## Read this first

- Follow [AGENTS.md](AGENTS.md) for instructions and event restrictions. This file records decisions and the last known state; verify anything that may have changed.
- Current phase: Corkathon build day, after the official 09:45 start. The 09:45–19:00 build window still applies; the supplied guide's isolated 09:00 reference is not permission to start early.
- All event times are Europe/Dublin.

## Current build status

- The Footfall MVP is now implemented in `footfall/` with Flask, SQLite, Jinja and a bounded saved-source refresh flow.
- Issue #11 has four selected Cork venue listing pages in `footfall/seed/sources.json`, each within 1 km, readable with the existing fetcher, and listing events in 7–13 Nov; twelve candidates are assessed in `footfall/seed/source_assessment.md`. All four selected robots paths allow the project user agent and all pages fetched as public HTML. Independent teammate review is pending.
- Issue #11 was merged into `main` through PR #23 on 2026-11-07 (squash commit `1fd4177`).
- Gate M1 was independently checked from Daniel's issue-12 screenshots and recorded on issue #12. The human baseline for issue #14 lists 11 visible entries across the four selected pages. PR #27 merged a local Ollama provider and reports a 4/4 live extraction run, including two in-window findings filtered by opening hours; detailed per-source output is not in the repo, so the row-level comparison remains open. The current workspace has no Ollama command or local daemon available.

## People and purpose

- Team 18: Daniel Marcinkowski, Olan Hennessy O'Flynn and Rajeev Shyam Kumar.
- This is Daniel's first hackathon. He wants continuing assistance, clear next steps and support with coordinating the team.
- Daniel is interested in PM/group-lead responsibilities. This is a proposal, not a team-agreed appointment. Roles remain open.

## Decisions made

| Topic | Decision |
| --- | --- |
| Repository | [meetdanielme/corkathon_team_18](https://github.com/meetdanielme/corkathon_team_18), private, default branch `main` |
| Tasks | GitHub Issues; one owner, observable acceptance criteria and real blockers per task. No additional PM tool for now. |
| Context | [Notion team page](https://app.notion.com/p/40fba34e944c8072b5e2cb90ac08bb37): concise goals, scope, roles, checkpoints, decisions and blockers. Avoid a duplicate task backlog. |
| Product | Footfall MVP: one independent Cork city-centre café, local event/weather signals, explainable preparation decisions and an owner-approved copied draft. |
| Stack | Python 3.11+, Flask 3, SQLite, Jinja and pytest; source refresh is bounded and synchronous. |
| Roles | Rajeev owns backend/frontend behaviour and templates; Daniel owns issues, design/CSS and demo; Olan owns source research and scout testing (design doc, 7 Nov). |
| Collaboration | Small branches/PRs, frequent integration, stable `main`. Review meaningful changes and verify the demo path. |
| Skills | Four shared Matt Pocock skills committed locally; no global installation needed. |

## Setup completed

- GitHub repository and initial planning documents were created; the app stack is recorded above.
- README includes the day plan and submission checklist. GitHub task and PR templates are in `.github/`.
- Notion skeleton was populated and read back: preparation checklist, goal/scope, people/ownership, checkpoints, decisions/blockers and submission readiness.
- Shared skill snapshots: `grill-me`, `grilling` (supporting skill), `to-tickets`, `handoff`; see [.agents/skills/README.md](.agents/skills/README.md).
- Canonical skill files live in `.agents/skills/`; `.claude/skills` is a relative symlink to them.
- GitHub ticket conventions are in [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md).
- Local `context/` contains organiser material and team files. It remains ignored, as do private `.agents/AGENTS.md` notes and credentials.

## AI assistance and handoffs

- Before substantial work, flag whether another usage channel would be a better fit. Keep small tasks moving here; avoid making Daniel manage every routine choice.
- Prepare a concise handoff when recommending a switch: goal, branch/commit, current state, relevant files/issues, constraints, done conditions, checks and next action. See [handoff template](docs/agents/handoff-template.md).
- Daniel has reported access to ChatGPT/Codex, Claude Pro, Claude API credit, Zed AI credit and Azure resources. Exact balances/reset counts belong only in ignored local notes; none has been verified live.
- The discussed strategy is subscription usage first, API/credit channels as tested fallbacks, and reserve capacity for late demo fixes. Do not switch billing channels or spend paid API credit without Daniel's direction.
- Changing an editor does not itself create a new provider allowance. Confirm live usage/reset information; do not promise a fixed number of hours or tasks.
- T3 Code was discussed as an optional interface, not selected or installed as part of this setup. No paid upgrade was agreed.

## Open items and immediate next steps

1. Teammate: independently check the four source records, 1 km distances, event dates, fetch output and access evidence in `footfall/seed/source_assessment.md`.
2. Team: agree whether the four-source starter directory is sufficient for the demo, then continue scout testing against the café radius and hours.
3. Keep README setup/run/check instructions aligned with the current implementation and verify the submission requirements on the day.

## Delivery reminders

- Suggested team targets: rough end-to-end flow by 12:30; feature freeze at 17:45; complete submission by 18:30.
- Official cutoff: 19:00. Submission needs a name, problem/solution, challenge selection, all members, judge-accessible repo and short demo video. Verify actual portal requirements on the day.
- Finalists pitch at 19:35: 3 minutes plus 2 minutes Q&A. Suggested story: problem → live demo → impact → next step.
- Keep a backup recording/screenshots. Arrange judge access before submitting; repository visibility and Notion publishing require user/team direction.
- Sources already consulted: supplied organiser email/guide and [Devpost event](https://corkathon.devpost.com/) / [rules](https://corkathon.devpost.com/rules), checked 5 November 2026. Confirmation email gives 09:00 check-in at the Common Room, the Quad, before moving to ORB Basement 02; reconfirm at arrival.

## Maintaining this file

Keep this a short current-state record. Update it when a decision, verified milestone or next step changes; distinguish proposals from agreements and date material changes. Do not paste chat logs, secrets, personal balances or a copy of the issue backlog. Link owning sources instead. Current user instructions and live verified sources take precedence over this snapshot.

## Azure provider direction — 7 November 2026

- Daniel authorized Azure setup through his CLI with a €5 setup/verification maximum, then explicitly selected Luna. Local configuration now selects Azure deployment `gpt-6-luna`; this supersedes the earlier Ollama/manual-chat selection for app AI usage. No automatic fallback or new infrastructure.
- Credentials live only in Daniel’s ignored local `.env`; never copy into shared docs. See [setup and run command](docs/team/azure-setup.md).
- Azure adapter verification and real-source refresh results are recorded in PR evidence. Future calls need to stay within Daniel’s authorized scope; request-token limits are not a currency hard cap.

- Verified Luna live refresh: four fetched sources, six stored events, two relevant insights; partial with three rejected findings. Known date-range/evidence-association limits in [setup report](docs/team/azure-setup.md); not a completed accuracy gate. No background server left running.

## Shared hosting — 7 November 2026

- Daniel requested one shared hosted demo and explicitly chose Vercel with Azure Luna. Vercel project `footfall-team18` uses Hobby; Turso Starter database of the same name is provisioned in Dublin after Daniel accepted marketplace terms. No App Service hosting was provisioned.
- Server-side secret configuration is in Vercel; remote libSQL preserves drafts/events across requests and instances. Public demo allowance is 20 lifetime Azure request reservations in the database, not a monetary hard cutoff. Do not raise/reset without Daniel’s direction.
- See [hosting operations and validation](docs/team/vercel-hosting.md). Shared-code deployment excludes the separate uncommitted visual work; source repo remains private. Share-link expiry and final verification are reported in the session.
