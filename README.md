# Link Check

**Public tool:** check links before you click — single URL, full SMS/email/chat, or **QR photo**. Good for smishing, phishing, delivery/bank impersonation, and “wrong company name” links (including hiring messages).

- **No URL fetch** in v0.1  
- **No cloud threat intel** by default  
- Plain English: brand/domain mismatch, defanged copy for notes  

Standalone from [Boundry MSSP](https://github.com/JsonCMorgan/boundry-ai-soc-platform). Recruiters and job seekers get one job, not a SOC dashboard.

---

## Public web app (Option 1)

```powershell
cd C:\Dev\link-check
pip install -e ".[public,dev]"
python public_app/app.py
```

Open **http://127.0.0.1:5055** (phone on same Wi‑Fi: `http://<your-pc-ip>:5055`).

### After local code changes

Flask does not always pick up template/CSS edits if an old process is still on **5055** (two listeners = stale UI in the browser).

```powershell
cd C:\Dev\link-check
.\scripts\restart-public-app.ps1
```

Then hard refresh the page (Ctrl+Shift+R). Background restart for agents: `.\scripts\restart-public-app.ps1 -Background`.

| Route | Purpose |
|--------|---------|
| `/` | Paste form |
| `/api/check` | `POST` JSON `{ "url" }`, `{ "message" }`, or `{ "qr_paste" }`, optional `claimed_brand` (QR image upload via form only in v0.1) |
| `/privacy` | Privacy copy |
| `/health` | Uptime probe |

### Deploy (pick one)

1. **Docker:** `docker build -t link-check .` → run on Fly.io / Railway / any host port 8080.  
2. **Gunicorn:** `gunicorn -b 0.0.0.0:8080 public_app.app:app`  
3. Set `PORT` env var (Railway/Render set this automatically).

Point a domain when ready (e.g. `linkcheck.yourdomain.com`). Update footer GitHub link after first push to `JsonCMorgan/link-check`.

---

## CLI (developers)

```bash
pip install -e ".[dev]"
python -m link_check "https://olivia.paradox.ai/x" --claimed "Intact Financial"
```

---

## Boundry integration (optional)

MSSP can `pip install -e` this package and use `link_triage.py`. Prefer the **public URL** for phone bookmarks once hosted.

---

## Brand data (feature 2)

- **Default employers:** `src/link_check/data/brands_default.json` (global: Amazon, Microsoft, carriers, etc.)
- **Optional packs:** `data/packs/canada_finance.json`, `tech_careers.json` (loaded automatically)
- Disable packs: env `LINK_CHECK_PACKS=none`. Custom list: `LINK_CHECK_PACKS=canada_finance`

## Paste full message (feature 1)

```bash
python -c "from link_check import analyze_message; import json; print(json.dumps(analyze_message('Intact jobs https://olivia.paradox.ai/x'), indent=2))"
```

## Limits

Does not prove malware. Flags **social engineering patterns** (e.g. “Intact” text → `paradox.ai` link). Third-party hiring vendors can be legitimate; always verify on the company’s **official** careers site.

## License

MIT