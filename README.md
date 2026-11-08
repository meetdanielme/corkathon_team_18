# Footfall

**Know what's happening. Prepare in time.**

Footfall helps small businesses spot local events that could affect demand, understand the evidence, and prepare before supplier deadlines.

Built by **[Daniel Marcinkowski](https://www.linkedin.com/in/meetdanielme/), [Olan Hennessy O'Flynn](https://www.linkedin.com/in/olan-hennessy-o-flynn-701a91373/) and [Rajeev Shyam Kumar](https://www.linkedin.com/in/rajeev-shyam-kumar-1859002a2/)** at Corkathon on 7 November 2026, at University College Cork. Footfall was shortlisted among the **top 9 of 26 projects**, and we pitched it to a jury with representatives from the UCC Computer Science Society, IGNITE @ UCC and FRAME.

[Try Footfall](https://footfall-team18.vercel.app/) · [Devpost project and walkthrough](https://devpost.com/software/footfall-0srjti)

## Why we built it

A café owner needs to decide what to order before they know how busy the next few days will be. A nearby graduation, concert or community event could change demand, but the useful information is scattered across websites and event calendars.

We wanted to connect that information to a practical decision: what deserves attention, why does it matter to this business, and when does the owner need to act?

Our first use case is an independent café in Cork. The wider idea is relevant to small businesses that depend on foot traffic.

## What it does

The experience is organised around the owner's week:

1. **See what's coming.** Review local events, weather context and supplier deadlines in a weekly timeline.
2. **Understand why it matters.** Inspect source evidence, event timing, distance, opening-hour overlap and uncertainty.
3. **Prepare before the cutoff.** Connect an insight to a supplier ordering deadline, or review a delivery clash with a nearby closure.
4. **Make the final call.** Create a supplier message, edit the recipient and wording, then approve and copy it to send yourself.

Owners can also update business locations and opening hours, edit supplier delivery schedules and cutoff rules, and revisit saved order messages.

To explore the hosted app, choose **Try the demo**, then **Continue with the demo café**. Sign-in and sign-up are simulated.

## How it works

Footfall combines model-assisted extraction with explicit application rules:

- A bounded source refresh fetches pages from a saved directory of local sources.
- An Azure-hosted language model extracts structured event information. The app validates the result before saving it and retains source links and supporting excerpts.
- Python rules calculate relevance using location, distance, trading hours and supplier cutoffs. Weather context and delivery access clashes add information to the planning flow.
- Supplier messages use constrained templates grounded in the selected insight and deadline. An optional model call chooses a wording style; it does not supply the message's factual claims.
- Refresh outcomes, missing information and uncertainty remain visible. Saved records are retained when a source refresh fails.

The goal is to help an owner make a decision they can understand and review.

### Stack

| Area | Tools |
| --- | --- |
| Application | Python, Flask |
| Interface | Server-rendered HTML, CSS and JavaScript |
| Local storage | SQLite |
| Hosted storage | Turso / libSQL |
| Hosting | Vercel |
| Hosted event extraction | Azure-hosted language model via the OpenAI Python SDK |

Local provider options include Azure, Ollama and Anthropic. The app also runs with saved events and deterministic message templates without a model provider.

## How we worked

We built Footfall as a three-person team during a one-day hackathon. We started with one user, one problem and a complete path from local information to a reviewed supplier message, then expanded the experience around that flow.

GitHub Issues held implementation tasks, with small branches and pull requests for integration. Shared project notes and handoffs helped carry context between tasks and AI sessions. Repository-local agent instructions and shared skills supported that workflow.

We used **Claude Opus 5.5, Sol 6.1 and Google's latest Gemini models**, choosing models for different tasks across the build. These were development tools, separate from the model calls made by Footfall itself.

Daniel used **T3 Code** to orchestrate his part of the work, including handing tasks between models when usage limits were reached. He set up the team workflow and led product and design: the weekly owner journey, app copy, landing and pricing pages, and simulated sign-up. His engineering work included Vercel and Turso deployment, bounded Azure calls, opening hours, order and supplier editing, message grounding, event deduplication, database reliability and page-load performance. He also prepared the submission materials.

Working together gave us a chance to take the idea through product decisions, implementation, integration and a live pitch in one day.

## Run locally

Use **Python 3.12** to match the hosted runtime.

```sh
git clone https://github.com/meetdanielme/corkathon_team_18.git
cd corkathon_team_18
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m scripts.reset_demo
flask --app "footfall.app:create_app()" run --debug
```

On Windows, create the environment with `py -3.12 -m venv .venv`, activate it with `.venv\Scripts\Activate.ps1` in PowerShell, and use `Copy-Item .env.example .env` to copy the configuration.

Open [localhost:5000](http://127.0.0.1:5000/). The default `FOOTFALL_LLM=none` configuration needs no API key. The reset command rebuilds the configured local database and loads prepared events; use it for a fresh local setup, as it removes existing local data.

For live event extraction, configure your own provider in `.env` using the placeholders in [`.env.example`](.env.example). The app loads this file automatically; existing environment variables take precedence. Keep credentials out of Git. Hosted API providers may incur charges; Ollama uses a locally running model.

Run the automated checks with:

```sh
python -m pytest -q
```

## Prototype scope

Footfall is a hackathon prototype, with a configured café profile, saved events and live source refreshes.

- **Accounts are simulated.** The public app shares business data; it is not an isolated account system. Use the supplied café rather than entering private business information.
- **Impact labels are heuristics.** They are not validated customer, footfall or revenue forecasts.
- **Coverage is limited.** No events found means none were found in the monitored sources, not that nothing is happening locally.
- **Saved records and supplier assumptions are not independently verified.** Source evidence and refresh status should inform how an insight is interpreted.
- **Approving a message does not send it or place an order.** The owner reviews, copies and sends it.
- **Pricing is a proposed commercial direction.** The prototype does not process payments.
- **Hosted model calls are bounded.** Live extraction can become unavailable when the shared allowance is exhausted; saved events and template messages remain usable.

## Explore the repository

| Path | Purpose |
| --- | --- |
| [`footfall/app.py`](footfall/app.py) | Flask routes and user flow |
| [`footfall/domain/`](footfall/domain/) | Relevance, opening hours, supplier cutoffs, clashes and message rules |
| [`footfall/scout/`](footfall/scout/) | Source fetching, extraction, validation and refresh |
| [`footfall/db.py`](footfall/db.py) | Storage and persistence |
| [`footfall/templates/`](footfall/templates/) and [`footfall/static/`](footfall/static/) | Interface and assets |
| [`footfall/seed/`](footfall/seed/) | Initial business profile, source directory and prepared events |
| [`tests/`](tests/) | Automated checks |
| [`docs/design/`](docs/design/) | Design and architecture notes |

Some supporting documents record decisions and checks from the build day. This README is the public introduction to the completed hackathon prototype.

## Credits

Built by [Daniel Marcinkowski](https://www.linkedin.com/in/meetdanielme/), [Olan Hennessy O'Flynn](https://www.linkedin.com/in/olan-hennessy-o-flynn-701a91373/) and [Rajeev Shyam Kumar](https://www.linkedin.com/in/rajeev-shyam-kumar-1859002a2/).

Footfall uses Flask, the OpenAI Python SDK, Turso/libSQL, Vercel and the other libraries listed in [`requirements.txt`](requirements.txt). Local event information comes from the source pages linked within the app; those organisations are information sources, not project partners.

Thanks to the Corkathon organisers, mentors and judges for the opportunity to build and share it.
