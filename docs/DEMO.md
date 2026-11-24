# Link Check — demo for recruiters & mentors

**Goal:** Show that you can triage a suspicious hiring link **without clicking it**, with optional live lookup of where the company really posts jobs.

**Audience:** Recruiters, hiring managers, mentors, friends job-hunting. Not a SOC product.

## Before the meeting (5 min)

1. `cd C:\Dev\link-check`
2. Free key (no card): https://serper.dev/signup → set `SERPER_API_KEY` in your user environment or session.
3. `.\scripts\restart-public-app.ps1`
4. On phone (same Wi‑Fi): `http://<your-pc-ip>:5055`
5. Hard refresh if the UI looks old.

**Free tier math:** Serper gives **2,500 searches** at signup. Even 20 live demos × 5 searches each = 100 queries. Plenty for months of coffee chats.

## 5-minute talk track

1. **Problem:** “They texted Intact / your bank / a carrier. The link looks official. You’re one tap from malware or a fake apply form.”
2. **Show Single URL** with a Paradox link + claimed **Intact Financial** → verdict explains vendor vs company site (offline).
3. **Turn on both checkboxes** → run again → point at **Live careers check** + **Web search (serper)** with real discovered URLs.
4. **Defanged line:** “This is for your notes, not ‘safe to click.’”
5. **Close:** “Start from the careers link search found, typed yourself. Not the SMS.”

## Canonical demo inputs

| Mode | Paste |
|------|--------|
| Single URL | `https://olivia.paradox.ai/candidates/apply/example` |
| Claimed | `Intact Financial` |
| Full message | Your real Intact SMS paste (with both paradox links) |

## What to say about privacy

- We **never** open the link they’re worried about.
- Web search sends **only the company name** to Serper (opt-in).
- Employer crawl hits **their domains only**.
- Full copy: `/privacy` on the app.

## If search isn’t configured

The app says to set `SERPER_API_KEY`. For offline-only demos, leave both checkboxes off; Intact + Paradox still tells a strong story.

## After demo

Point them at the GitHub repo or your deployed URL when you have one. MSSP `/ops/link-check` is **not** the public pitch.