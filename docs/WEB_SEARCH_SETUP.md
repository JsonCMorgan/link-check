# Web search setup (Stage 2)

Link Check can search the web for **official careers links** when the user opts in. Your pasted suspicious link is **never** sent to the search provider. Only the company name (and optional known domain) is used in the query.

## Pick a provider (first match wins)

| Provider | Free tier | Signup | Env var |
|----------|-----------|--------|---------|
| **Serper** (recommended to start) | **2,500 queries once**, no credit card | https://serper.dev/signup | `SERPER_API_KEY` |
| **Brave Search API** | **~1,000 searches/month** ($5 credit/mo; card required, can set $0 prepay) | https://api-dashboard.search.brave.com | `BRAVE_SEARCH_API_KEY` |
| **SearXNG** (self-hosted, privacy-max) | Free on your machine | Docker: https://docs.searxng.org/admin/installation.html | `SEARXNG_URL` (e.g. `http://127.0.0.1:8888`) |

Priority: `SERPER_API_KEY` → `BRAVE_SEARCH_API_KEY` → `SEARXNG_URL`.

## Local dev (PowerShell)

```powershell
cd C:\Dev\link-check
$env:SERPER_API_KEY = "your-key-here"
.\scripts\restart-public-app.ps1
```

For a persistent key on Jason's PC, put the var in your user environment or a local `.env` loader (do not commit keys).

## Production

Set the same env var on Fly/Railway/Render. Rate-limit abuse at the app layer (already per-IP).

## Privacy

- Opt-in checkbox: **Search the web for careers links**
- Query example: `Intact Financial official careers site OR site:intact.ca careers`
- Serper/Brave are **third parties**; SearXNG stays on your infra if self-hosted.

## Google Custom Search JSON API

Closed to **new** customers in 2026, sunsets **2027-01-01**. Not recommended for new installs.