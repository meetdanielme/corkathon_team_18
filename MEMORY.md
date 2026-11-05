# Team memory

Last updated: 5 November 2026. Shared project context, not a chat transcript.

## Read this first

- Follow [AGENTS.md](AGENTS.md) for instructions and event restrictions. This file records decisions and the last known state; verify anything that may have changed.
- Current phase: preparation only. No project code, scaffold or application tests have been written. Project implementation must wait until 09:45 on Saturday 7 November 2026.
- All event times are Europe/Dublin. Official rules specify a 09:45–19:00 build window; the supplied guide also contains an isolated 09:00 reference. Use 09:45 unless organisers clarify otherwise.

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
| Product | Choose after the sponsor brief. Start with one user, one problem and one end-to-end demo flow. |
| Stack | Undecided. Prefer familiar tools, open source, free plans and student benefits. |
| Collaboration | Small branches/PRs, frequent integration, stable `main`. Review meaningful changes and verify the demo path. |
| Skills | Four shared Matt Pocock skills committed locally; no global installation needed. |

## Setup completed

- GitHub repository created and initial planning documents pushed. No application stack or CI has been selected.
- README includes the day plan and submission checklist. GitHub task and PR templates are in `.github/`.
- Notion skeleton was populated and read back: preparation checklist, goal/scope, people/ownership, checkpoints, decisions/blockers and submission readiness.
- Shared skill snapshots: `grill-me`, `grilling` (supporting skill), `to-tickets`, `handoff`; see [.agents/skills/README.md](.agents/skills/README.md).
- Canonical skill files live in `.agents/skills/`; `.claude/skills` is a relative symlink to them. Matching global copies installed during this preparation were removed.
- GitHub ticket conventions are in [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md).
- Local `context/` contains the organiser email/context, Hacker Guide PDF and team spreadsheet. It remains ignored, as do private `.agents/AGENTS.md` notes and credentials.
- GitHub connector repository creation failed with a token-permission error; the authenticated `gh` CLI succeeded. The `ntn` CLI successfully edited/read the Notion page. Check current access before reuse.

## AI assistance and handoffs

- Before substantial work, flag whether another usage channel would be a better fit. Keep small tasks moving here; avoid making Daniel manage every routine choice.
- Prepare a concise handoff when recommending a switch: goal, branch/commit, current state, relevant files/issues, constraints, done conditions, checks and next action. See [handoff template](docs/agents/handoff-template.md).
- Daniel has reported access to ChatGPT/Codex, Claude Pro, Claude API credit, Zed AI credit and Azure resources. Exact balances/reset counts belong only in ignored local notes; none has been verified live.
- The discussed strategy is subscription usage first, API/credit channels as tested fallbacks, and reserve capacity for late demo fixes. Do not switch billing channels or spend paid API credit without Daniel's direction.
- Changing an editor does not itself create a new provider allowance. Confirm live usage/reset information; do not promise a fixed number of hours or tasks.
- T3 Code was discussed as an optional interface, not selected or installed as part of this setup. No paid upgrade was agreed.

## Open items and immediate next steps

1. Daniel/team: confirm GitHub collaborator access, Notion sharing and Devpost registration. These were not performed by the assistant; completion is unverified.
2. Team: compare strengths, agree coordination/roles and bring 2–3 ideas rather than a locked plan.
3. Daniel: verify current AI headroom and test fallbacks on unrelated work before Saturday. No project implementation during preparation.
4. At the 09:30 brief: record the actual challenge, judging criteria and any rule changes. Neither challenge nor criteria is known yet.
5. From 09:45: timebox idea grilling, agree a small MVP and stack, then draft/approve GitHub tickets with `to-tickets`.
6. After choosing the stack: document real setup/run/check commands in README; they do not exist yet.

## Delivery reminders

- Suggested team targets: rough end-to-end flow by 12:30; feature freeze at 17:45; complete submission by 18:30.
- Official cutoff: 19:00. Submission needs a name, problem/solution, challenge selection, all members, judge-accessible repo and short demo video. Verify actual portal requirements on the day.
- Finalists pitch at 19:35: 3 minutes plus 2 minutes Q&A. Suggested story: problem → live demo → impact → next step.
- Keep a backup recording/screenshots. Arrange judge access before submitting; repository visibility and Notion publishing require user/team direction.
- Sources already consulted: supplied organiser email/guide and [Devpost event](https://corkathon.devpost.com/) / [rules](https://corkathon.devpost.com/rules), checked 5 November 2026. Confirmation email gives 09:00 check-in at the Common Room, the Quad, before moving to ORB Basement 02; reconfirm at arrival.

## Maintaining this file

Keep this a short current-state record. Update it when a decision, verified milestone or next step changes; distinguish proposals from agreements and date material changes. Do not paste chat logs, secrets, personal balances or a copy of the issue backlog. Link owning sources instead. Current user instructions and live verified sources take precedence over this snapshot.
