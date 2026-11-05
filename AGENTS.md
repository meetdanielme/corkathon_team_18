# Corkathon Team 18

## Event constraints

- Event: Saturday 7 November 2026, UCC. All times Europe/Dublin.
- Before 09:45 on event day: planning, research, sketches and tool setup only. Do not generate project code, scaffolds, application tests or project implementation in advance.
- Official build window: 09:45–19:00. Confirm live organiser instructions; do not treat the guide's isolated 09:00 reference as permission to start early.
- Challenge tracks and judging criteria are not yet known. Record them after the 09:30 brief; do not invent requirements.
- Target a complete Devpost submission at 18:30; hard deadline 19:00. Include challenge, team, repo, description and short demo video. Finalist pitch: 3 minutes plus 2 minutes Q&A.

## Team and scope

- Team: Daniel Marcinkowski, Olan Hennessy O'Flynn, Rajeev Shyam Kumar. Roles and stack remain team decisions; Daniel's interest in coordinating is not an agreed appointment.
- Team alignment: https://app.notion.com/p/40fba34e944c8072b5e2cb90ac08bb37
- Keep Notion concise: user/problem, MVP, owners, checkpoints, decisions. Track implementation tasks in GitHub Issues rather than duplicating a backlog.
- Build one demonstrable end-to-end flow first. Prefer small changes, frequent integration and a stable main branch. Target feature freeze at 17:45.
- Each task needs one owner and an observable done condition. Raise blockers early; seek a mentor after about 20 minutes stuck.
- Document actual run/setup/check commands in README after the team chooses the stack. Use relevant checks; do not add infrastructure without a concrete need.

## Tooling

- Prioritize open source, free plans and GitHub Student Developer Pack options. Prefer established project tooling. Consider free/student options before paid services or new hosted infrastructure.
- Prefer rg/fd, bat, jq/yq, ruff, shellcheck/shfmt and the project's package manager when available; standard tools are acceptable fallbacks.

## Data and delivery

- Keep context/, personal contact details, the full team roster, credentials and .env files out of Git. Never commit API keys; provide placeholder-only .env.example if needed on the day.
- Use synthetic or authorized data. Credit reused libraries, APIs, datasets and assets; respect licences and event rules.
- Before submission, verify judge access to the repo/video/demo and rehearse the actual flow. Prepare a backup recording; accurately distinguish implemented features from future ideas.
- Do not publish the private Notion page or change repository visibility without team/user direction.
