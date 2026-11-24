# Link Check (offline)

Check a URL **before you click** — brand/domain mismatch, basic phish heuristics, defanged copy. **No URL fetch, no cloud API** in v0.1.

## CLI (computer)

```bash
pip install -e ".[dev]"
python -m link_check "https://olivia.paradox.ai/candidates/apply/x" --claimed "Intact Financial"
python -m link_check "https://careers.intact.ca/job" --claimed "Intact Financial" --json
```

## Boundry API (phone on home LAN)

With Flask running on your PC and phone on the same network (or Tailscale):

- **Page:** `http://<your-pc>:5000/ops/link-check`
- **API:** `POST /api/ops/link-check`  
  JSON: `{"url": "...", "claimed_brand": "Intact Financial"}`

## iOS Shortcut (sketch)

1. **Get Contents of URL** — POST to `http://10.x.x.x:5000/api/ops/link-check`  
   Headers: `Content-Type: application/json`  
   Body: `{"url": "<Shortcut Input>", "claimed_brand": "<optional>"}`  
   (You must be logged into Boundry in Safari first, or add a personal API token later.)
2. **Get Dictionary Value** `plain_summary` from JSON.
3. **Show Result**.

Easier path: Shortcut **Open URL** → `http://<pc>:5000/ops/link-check` and paste in the form.

## Limits

- Does not prove malware; flags **obvious social-engineering patterns** (wrong domain for claimed brand).
- Third-party hiring links (e.g. Paradox) can be legitimate — output tells you to verify on the official site.

## License

MIT