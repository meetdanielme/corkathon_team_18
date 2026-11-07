# Shared Vercel demo with Azure Luna

Project: `meetdanielme/footfall-team18` (Hobby). Database: Turso `footfall-team18`, Starter ($0/month), Dublin region. AI: existing Azure `gpt-6-luna` deployment. No Azure App Service resources were created.

## Architecture

Vercel runs the Flask WSGI entry point in `app.py`. Azure credentials and the Flask secret are server-side Vercel secrets, never bundled into HTML or Git. Turso uses remote libSQL, so event, weather and draft changes persist across requests, function instances and deployments. Local runs retain ordinary SQLite when no Turso URL is configured. A Vercel deployment without Turso fails clearly instead of silently losing data to a temporary SQLite file.

`python scripts/prepare_vercel.py` copies the Flask static assets to `public/static` for Vercel CDN delivery. Python is pinned to 3.12. Per-function duration is 180 seconds; source refresh remains bounded to 90 seconds and four source-model calls per refresh.

## AI allowance

The public demo has a shared **40-call lifetime allowance**, reserved atomically in Turso before each Azure request. This is shared across visitors and deployments, so cold starts cannot reset it. Failed attempts count conservatively. SDK retries are disabled, timeout is 60 seconds, completion length is at most 2048 tokens. The allowance is an abuse/spend bound, not an Azure-enforced €5 cutoff or an exact currency meter. Once exhausted, live extraction reports errors and drafts retain deterministic templates. Prepared mode stays usable.

Do not reset the allowance or raise the setting without Daniel’s direction. Do not enable paid Vercel or Turso plans. Azure usage consumes Daniel’s credit; a free host does not make model calls free.

## Deployment and source

The Vercel project is connected to the private GitHub repository `meetdanielme/corkathon_team_18`. **Every push or merged PR to `main` automatically builds a production deployment and updates https://footfall-team18.vercel.app .** The production branch is `main`, and automatic domain assignment is enabled. Feature branches receive preview deployments; use the stable production URL for the team/judge demo.

The new attention design and subsequent fixes are merged into main and included in production. Repository visibility remains private, and Vercel public-source access is disabled. Visitors to the production URL do not need a Vercel login, Azure credentials, or an expiring share link.

Deploy changes through a branch and PR into main. No local `vercel deploy` command, GitHub Actions workflow, copied credentials, or personal access token is required for the normal deployment path. If an automatic build fails, Vercel retains the previous successful production deployment; inspect the GitHub check and Vercel build logs before retrying.

For an explicitly requested manual recovery deployment only:

```sh
vercel project inspect --non-interactive
vercel deploy --prod --yes
```

Credentials must already exist in the target Vercel project. Another project or account needs its own authorized secrets and remote database; cloning alone never grants use of Daniel’s Azure credential.

## Validation

- 50 tests pass, including native libSQL row/draft compatibility, reconnect persistence, exhausted allowance and per-refresh call accounting on a reused worker.
- Real Turso: schema and fictional profile seeded, seven prepared records stored, draft read over a separate connection.
- Hosted home, CDN CSS, API, draft creation, editing, approval and separate-request persistence checked.
- Hosted live refresh is verified separately against Azure and the four saved sources. Honest source validation errors remain visible; deployment is not extraction-accuracy signoff.
- Initial hosted test exposed a remote transaction idle/lock issue. Refresh now commits the source-attempt timestamp before network/model calls. The model call budget is calculated per refresh, rather than lifetime of a warm worker.
- Prepared source records remain labelled fictional. All users of this single demo share the same fictional café and draft records; this is not a multi-tenant account system.

Daniel explicitly increased the shared allowance to 40 total calls on 7 November after diagnosing refresh warnings. Remote connections are renewed after network/model work, at a committed boundary; writes are never blindly retried.
