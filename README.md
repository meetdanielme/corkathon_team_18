# Corkathon · Team 18

Saturday 7 November 2026 · UCC · Planning stage

**No project code before hacking starts at 09:45.** Tracks and judging criteria are announced on the day. Confirm any changes at the opening.

## Team workspace

- [Shared agent memory](MEMORY.md) — decisions, setup status and next steps; agents start with [AGENTS.md](AGENTS.md).
- [Team alignment page](https://app.notion.com/p/40fba34e944c8072b5e2cb90ac08bb37) — goals, roles, scope and decisions.
- GitHub Issues — implementation tasks, each with one owner and a clear done condition.
- [Devpost](https://corkathon.devpost.com/) — submission by **19:00 Europe/Dublin**.
- Team: Daniel Marcinkowski, Olan Hennessy O'Flynn, Rajeev Shyam Kumar. Roles to agree together.

## Before Saturday

- Join the event on Devpost; check GitHub access for all three teammates.
- Test tools on an unrelated throwaway project. Bring laptop, charger and student ID.
- Compare strengths and bring 2–3 problem ideas. Choose the stack together after the brief.

## Working together

Shared AI skills are included in [`.agents/skills/`](.agents/skills/README.md); Claude Code uses the same files via `.claude/skills`. Start a fresh agent session after cloning to discover them.

1. Pick one user, one problem and one end-to-end demo flow.
2. Take a small issue; agree interfaces before splitting work.
3. Use short branches (`feat/short-name`, `fix/short-name`) and small pull requests into `main`.
4. Ask for a quick teammate review; keep `main` runnable. Integrate throughout the day.
5. Add exact setup, run and validation commands here once the stack exists.

## Day plan

| Time | Milestone |
| --- | --- |
| 09:00 | Check-in: Common Room, the Quad (confirmation email); then ORB Basement 02 |
| 09:30 | Capture challenge, judging criteria and submission rules |
| 09:45–10:30 | Agree problem, MVP, roles and demo story |
| 12:30 | Target: rough end-to-end flow |
| 17:45 | Feature freeze; prepare demo, video and submission |
| 18:30 | Submit a complete entry; verify links and access |
| 19:00 | Official submission deadline |
| 19:35 | Finalists: 3-minute pitch + 2-minute Q&A |

## Submission checklist

- [ ] Project name, problem, solution and challenge prompt
- [ ] All team members added
- [ ] Repository link accessible to judges
- [ ] Short demo video uploaded and link tested
- [ ] Working demo and backup screenshots/recording
- [ ] Dependencies, APIs, data and other reused assets credited
- [ ] Submission saved before 19:00

The repository starts private. Agree visibility or judge access before submission. Local `context/` contains supplied material and personal details; it is intentionally excluded from Git.

Sources: supplied organiser email and Hacker Guide; [official rules](https://corkathon.devpost.com/rules) and [event page](https://corkathon.devpost.com/), checked 5 November 2026. The guide mentions 09:00 in one rule; official rules specify project work from 09:45. Use 09:45 unless organisers clarify otherwise.

## Shared hosted demo

Footfall can run on Vercel with Azure Luna and persistent Turso storage. See [hosting setup, limits and validation](docs/team/vercel-hosting.md). Local SQLite remains available; Azure/Turso credentials are supplied only through server environment variables. Deployment changes are in PR #29.
