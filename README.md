# ProspectKit 🔍

**Free, open-source contact enrichment for GTM teams.**

Paste a LinkedIn URL → get verified email + phone number in seconds.
Self-host in 3 commands. Deploy to the cloud for free. Bring your own Apollo API key.

![ProspectKit screenshot](https://raw.githubusercontent.com/your-username/prospectkit/main/screenshot.png)

---

## Features

- **LinkedIn URL lookup** — paste any LinkedIn profile URL and get contact info instantly
- **Name + company search** — no LinkedIn URL? Search by name
- **Bulk enrichment** — up to 20 contacts at once with CSV export
- **Email verification** — Verified / Likely Valid / Not Found confidence scores
- **Your API key, your data** — key lives in your browser, never stored on any server
- **One-command setup** — no Docker, no database, no config files

---

## Run locally (3 steps)

**Prerequisites:** Python 3.9+ and a free [Apollo API key](https://app.apollo.io/#/settings/integrations/api)

```bash
# 1. Clone
git clone https://github.com/your-username/prospectkit.git
cd prospectkit

# 2. Start
./start.sh

# 3. Open
# Go to http://localhost:8000 — you'll be prompted to enter your Apollo key
```

That's it. No `.env` files, no config — just paste your Apollo key in the UI on first load.

---

## Deploy for your team (free, always-on)

### Render (recommended — free tier)

1. Fork this repo
2. Go to [render.com](https://render.com) → New → Web Service → connect your fork
3. Add environment variable: `APOLLO_API_KEY = your_key`
4. Deploy → share the URL with your team

### Railway

1. Fork this repo
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variable: `APOLLO_API_KEY = your_key`
4. Deploy → share the URL

> When `APOLLO_API_KEY` is set server-side, the team doesn't need to enter their own key — it just works.

---

## Get an Apollo API key

1. Sign up free at [app.apollo.io](https://app.apollo.io)
2. Go to **Settings → Integrations → API**
3. Copy your key — paste it into ProspectKit on first launch

Apollo's free plan includes 50 enrichments/month. Paid plans start at $49/mo for unlimited.

---

## Accuracy

| Badge | Meaning |
|---|---|
| 🟢 Verified | Apollo has confirmed email deliverability |
| 🟡 Likely Valid | Best guess based on known patterns |
| 🔴 Not Found | No email on file |

For best results, always use a LinkedIn URL. Name-only lookups are less accurate.

---

## Tech stack

- **Backend:** Python + FastAPI
- **Frontend:** Vanilla JS + Tailwind CSS
- **Data:** Apollo.io People Match API

---

## Built by

Made by [Sabrina Lu](https://www.linkedin.com/in/your-profile) — GTM operator sharing open-source tools for revenue teams.

Follow for more: [LinkedIn](https://linkedin.com/in/your-profile) · [GitHub](https://github.com/your-username)

---

*If this saved you time, a ⭐ on GitHub goes a long way.*
