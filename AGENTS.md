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

## Agent skills

- Use GitHub Issues for `to-tickets`; see `docs/agents/issue-tracker.md`. Notion holds context, goals and decisions, not a second task backlog.
- Keep planning proportional to this one-day event. Timebox idea grilling; prefer a few small, independently verifiable tickets. Present the proposed breakdown before publishing.

## Assistant and AI usage

- Act as Daniel's continuing assistant: state the next concrete steps clearly, distinguish Daniel's actions from assistant actions, and finish each substantive update with the immediate next step.
- Before a substantial job that could use another AI channel, briefly state the proposed scope, recommended channel and reason. Consider whether a smaller model or narrower task would suffice.
- If recommending a different channel, prepare a concise, copyable handoff before implementation: goal, constraints, repo/branch, relevant files or issue links, current state, acceptance criteria, validation commands, and the next action. Include no secrets. Do not run the same job twice in parallel.
- Account balances and reset counts are private, changeable context. Consult Daniel's local `.agents/AGENTS.md` when available; check before relying on any reported balance.
- Preserve manual resets for event-day work. Claude API credit is a separate fallback from Claude Pro; distinguish subscription authentication from API billing. Never switch billing, enable paid overages or spend API/Azure credit without Daniel's direction for that channel.
- Keep ordinary small work moving here. Flag substantial implementation, long debugging loops or repeated reviews early enough to preserve a useful handoff; do not wait until limits are exhausted.
