"""Extract URLs and inferred employer names from SMS/email paste."""

from __future__ import annotations

import re
from typing import Any

from link_check.analyze import analyze_link
from link_check.brands import brand_registry, resolve_brand

_URL = re.compile(
    r"(?i)\b(?:https?://[^\s<>\"']+|www\.[a-z0-9][\w.-]+\.[a-z]{2,}(?:/[^\s]*)?)",
)

_RISK_RANK = {"high": 3, "elevated": 2, "caution": 1, "low": 0}


def extract_urls(text: str) -> list[str]:
    """Unique URLs from message text, normalized with https when needed."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _URL.findall(text or ""):
        u = m.strip().rstrip(".,);]")
        if u.lower().startswith("www."):
            u = "https://" + u
        key = u.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(u)
    return out


def infer_claimed_brand(text: str) -> str:
    """
    If a known employer display name appears in the paste, return the longest match.
    """
    blob = (text or "")
    if not blob.strip():
        return ""
    registry = brand_registry()
    hits: list[tuple[int, str]] = []
    for row in registry.values():
        disp = (row.get("display") or "").strip()
        if len(disp) < 3:
            continue
        if disp.lower() in blob.lower():
            hits.append((len(disp), disp))
    if hits:
        hits.sort(reverse=True)
        return hits[0][1]
    m = re.search(
        r"(?i)\b(?:from|at|with)\s+([A-Z][A-Za-z0-9&.'\s-]{2,48}(?:Financial|Insurance|Corp|Inc|Ltd|Bank|Group)?)",
        blob,
    )
    if m:
        return m.group(1).strip().rstrip(".,")
    return ""


def analyze_message(text: str, *, claimed_brand: str = "") -> dict[str, Any]:
    """Analyze every URL in a message; merge inferred employer name."""
    raw = (text or "").strip()
    if not raw:
        return {"ok": False, "error": "Paste a message that contains at least one link."}

    urls = extract_urls(raw)
    if not urls:
        return {
            "ok": False,
            "error": "No http(s) or www link found. Paste the full text including the URL.",
        }

    inferred = (claimed_brand or "").strip() or infer_claimed_brand(raw)
    effective = inferred

    results: list[dict[str, Any]] = []
    for u in urls:
        row = analyze_link(u, claimed_brand=effective)
        if row.get("ok"):
            results.append(row)

    if not results:
        return {"ok": False, "error": "Could not analyze links in this message."}

    worst = max(results, key=lambda r: _RISK_RANK.get(r.get("risk_level") or "low", 0))
    multi = len(results) > 1

    if multi:
        summary = (
            f"Found {len(results)} links. Highest concern: {worst.get('plain_summary') or worst.get('host')}"
        )
    else:
        summary = worst.get("plain_summary") or ""

    if inferred and not claimed_brand:
        summary = f"Inferred employer from text: {inferred}. " + summary

    return {
        "ok": True,
        "mode": "message",
        "message_preview": raw[:500],
        "urls_found": urls,
        "inferred_claimed": inferred,
        "claimed_override": claimed_brand or "",
        "results": results,
        "worst": worst,
        "plain_summary": summary,
        "risk_level": worst.get("risk_level"),
        "verdict": worst.get("verdict"),
        "offline": True,
    }