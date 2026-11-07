# Azure AI setup on Daniel’s machine

Use the existing Azure OpenAI deployment **gpt-6-luna** in `meetdanielme-azure-ai`, resource group `ai`, France Central. No new Azure resource or deployment was created. Daniel authorized a €5 maximum for setup/verification on 7 November 2026; that is not an ongoing spend authorization or an Azure-enforced billing cutoff.

The Azure CLI supplied the existing resource key directly to ignored `.env` (mode 0600). Never paste it into Git, issues or chat. `FOOTFALL_LLM=azure` selects Azure deliberately; there is no automatic provider fallback.

## Run the current visual-design checkout

From `/Users/danielmarcinkowski/Documents/Developer/corkathon_team_18`:

```sh
uv run --no-project --env-file .env --python .venv/bin/python python -m flask --app "footfall.app:create_app()" run --port 5059
```

The command loads `.env` even in the older visual checkout, which lacks merged main’s automatic env loader. Stop with Ctrl-C. No server is left running by setup. Use a foreground terminal; future Refresh clicks use Azure credits.

The older visual checkout still has two EXAMPLE ROW sources. It needs the team’s merged real-source changes integrated before its default fresh database can demonstrate the four real sources. Do not discard or blindly rebase the uncommitted visual work. The isolated `feat/azure-app-setup` checkout uses the four merged source records for verification.

## Local verification evidence

See `output/azure-verification/luna-result.json` for the actual source run and per-source errors/limitations. Its isolated database is `output/azure-verification/luna-verified.sqlite3`; neither file is committed. The prior GPT-5.4 result is a preliminary test superseded by Daniel’s explicit Luna selection.

## Request limits

Azure calls have a 60-second timeout, no automatic SDK retries, and at most 2048 completion tokens per call by default. `.env` selects `AZURE_OPENAI_REASONING_EFFORT=none`; the adapter omits temperature for reasoning-model compatibility. These are request bounds, not a cumulative currency budget. Do not leave refresh loops or unattended processes running.

To use prepared-only mode without model spending:

```sh
uv run --no-project --env-file .env --python .venv/bin/python env FOOTFALL_LLM=none python -m flask --app "footfall.app:create_app()" run --port 5059
```

Another teammate needs their own authorized local credentials. No secret is stored in this document or PR.

## Verified Luna result (7 November 2026)

The adapter returned valid JSON with `gpt-6-luna`. The actual Flask live-refresh endpoint returned HTTP 200: four sources fetched successfully, six events stored, two relevant insights, four exclusions. The run is **partial**, with three rejected findings (two outside the date window and one non-verbatim excerpt). This verifies the Azure integration, not complete extraction accuracy.

Quality limitations observed: cinema date ranges were represented with date-only midnight endpoints; one cinema finding was attached to a neighbouring title’s excerpt. The current validator accepts verbatim text without proving it belongs to the named event. These require source-review work before using those records for a pitch. The two relevant insights were the Calaverita workshop and Harry Clarke lecture. No model-generated attendance was stored.

Tests: merged-main checkout 47 passed; existing visual checkout tests also pass. No server or model loop was left running. Preliminary GPT-5.4 verification made three calls before Daniel selected Luna; Luna verification made one ping and four source calls. Exact billed spend has not been reconciled against Azure’s delayed billing records.
