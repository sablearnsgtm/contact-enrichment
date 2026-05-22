# ProspectKit 🔍

**Free, open-source contact enrichment for GTM teams.**

Paste a LinkedIn URL → get verified email + phone in seconds.  
Works with Apollo, Hunter.io, and Prospeo — run them as a waterfall for maximum hit rate.  
Self-host in 3 commands. Deploy to the cloud free. Bring your own API keys.

![ProspectKit screenshot](https://raw.githubusercontent.com/sablearnsgtm/contact-enrichment/main/screenshot.png)

---

## Features

- **LinkedIn URL lookup** — paste any LinkedIn profile URL and get contact info instantly
- **Multi-provider waterfall** — Apollo → Hunter.io → Prospeo, tries each in order until a match
- **Drag to reorder** — set your own provider priority in the settings UI
- **Name + company search** — no LinkedIn URL? Search by name + domain
- **Bulk enrichment** — up to 20 contacts at once with CSV export
- **Email verification** — Verified / Likely Valid / Not Found confidence scores
- **Your API key, your data** — keys live in your browser, never stored on any server
- **One-command setup** — no Docker, no database, no config files

---

## Run locally (3 steps)

**Prerequisites:** Python 3.9+ and at least one free API key (Apollo, Hunter.io, or Prospeo)

```bash
# 1. Clone
git clone https://github.com/sablearnsgtm/contact-enrichment.git
cd contact-enrichment

# 2. Start
./start.sh

# 3. Open
# Go to http://localhost:8000 — paste your API key in the Sources panel on first load
```

That's it. No `.env` files, no config — just add your key in the UI.

---

## Deploy for your team (free, always-on)

### Render (recommended — free tier)

1. Fork this repo
2. Go to [render.com](https://render.com) → New → Web Service → connect your fork
3. Optionally add env vars so your team doesn't need to enter keys themselves:
   ```
   APOLLO_API_KEY = your_key
   HUNTER_API_KEY = your_key
   PROSPEO_API_KEY = your_key
   ```
4. Deploy → share the URL with your team

### Railway

1. Fork this repo
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add the same environment variables above
4. Deploy → share the URL

---

## Data sources

| Provider | Best for | Free tier | Get key |
|---|---|---|---|
| Apollo | LinkedIn URL → email + phone | 50/mo | [app.apollo.io](https://app.apollo.io/#/settings/integrations/api) |
| Hunter.io | Name + company domain → email | 25/mo | [hunter.io/api-keys](https://hunter.io/api-keys) |
| Prospeo | LinkedIn URL → email (high accuracy) | 75/mo | [prospeo.io/api](https://prospeo.io/api) |

You don't need all three — one is enough to get started. Add more to improve hit rate.

---

## Using Clay?

Clay is an enrichment orchestrator, not a direct API. Two ways to connect:

1. **Export from Clay** → paste URLs into the Bulk tab
2. **Clay webhook** → point a Clay HTTP enrichment step at `POST /enrich` with an `X-Provider-Keys` header containing your keys as JSON

---

## Accuracy

| Badge | Meaning |
|---|---|
| 🟢 Verified | Provider has confirmed email deliverability |
| 🟡 Likely Valid | Best guess based on known patterns |
| 🔴 Not Found | No email on file |

For best results, always use a LinkedIn URL. Name-only lookups are less accurate.

---

## Adding a new provider

Drop a file in `providers/`, subclass `BaseProvider`, implement `enrich()`, register it in `providers/__init__.py`. That's it — the waterfall picks it up automatically.

---

## Tech stack

- **Backend:** Python + FastAPI
- **Frontend:** Vanilla JS + Tailwind CSS
- **Data:** Apollo · Hunter.io · Prospeo (pluggable)

---

## Built by

Made by [Sabrina Lu](https://www.linkedin.com/in/sabrina-lu) — GTM operator sharing open-source tools for revenue teams.

Follow for more: [LinkedIn](https://www.linkedin.com/in/sabrina-lu) · [GitHub](https://github.com/sablearnsgtm)

---

*If this saved you time, a ⭐ on GitHub goes a long way.*
