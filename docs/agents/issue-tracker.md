# Issue tracker: GitHub

Repository: https://github.com/meetdanielme/corkathon_team_18

- Issues and implementation tickets live in this repository's GitHub Issues. Prefer the authenticated `gh` CLI. Verify the target with `gh repo view --json nameWithOwner` before publishing.
- Notion holds the challenge brief, team goals, roles, context and decisions. Link relevant context from tickets rather than duplicating a backlog.
- For `to-tickets`, draft a small set of end-to-end slices; show the titles, done conditions and blockers to Daniel before publishing.
- Each ticket needs one owner, a clear user-visible outcome and acceptance criteria. Use native blocking dependencies where available, otherwise include `Blocked by: #number` in the body.
- Use existing labels when useful; do not require a triage system or add `ready-for-agent` automatically. Team members may own tickets directly.
- Read tickets with `gh issue view NUMBER --json number,title,body,labels,comments`. Create with `gh issue create --title TITLE --body-file PATH` to preserve multiline text.
- Check existing issues before creating new ones. Do not close or modify parent issues as a side effect of ticket generation. PRs are not a separate request/triage surface.
- No project implementation before the event build window. The challenge, stack and implementation backlog remain undecided until the team hears the brief.
