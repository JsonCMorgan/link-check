"""Brand-to-domain expectations (offline, user-editable table)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Recruiters often use these; link is not automatically malicious.
RECRUITING_VENDOR_SUFFIXES = (
    "paradox.ai",
    "myworkdayjobs.com",
    "greenhouse.io",
    "lever.co",
    "icims.com",
    "taleo.net",
    "smartrecruiters.com",
)

# Common SMB / hire-target brands (expand over time).
DEFAULT_BRANDS: dict[str, dict[str, Any]] = {
    "intact": {
        "display": "Intact Financial",
        "domains": (
            "intact.ca",
            "intact.com",
            "intact.net",
            "intactfinancial.com",
            "intactfc.com",
        ),
    },
    "microsoft": {
        "display": "Microsoft",
        "domains": ("microsoft.com", "microsoftonline.com", "live.com", "office.com"),
    },
    "google": {
        "display": "Google",
        "domains": ("google.com", "youtube.com", "gmail.com"),
    },
}


def _normalize_brand_key(name: str) -> str:
    n = (name or "").lower()
    for ch in ".,'\"()-":
        n = n.replace(ch, " ")
    return " ".join(n.split())


def resolve_brand(claimed: str) -> dict[str, Any] | None:
    """Match claimed company text to a brand record."""
    if not claimed:
        return None
    key = _normalize_brand_key(claimed)
    for bid, row in DEFAULT_BRANDS.items():
        disp = _normalize_brand_key(row.get("display") or "")
        if bid in key or key in disp or disp in key:
            return {**row, "id": bid}
    if "intact" in key:
        return {**DEFAULT_BRANDS["intact"], "id": "intact"}
    return None


def host_matches_brand(host: str, brand: dict[str, Any]) -> bool:
    """True if host is the brand domain or a subdomain of it."""
    if not host or not brand:
        return False
    for dom in brand.get("domains") or ():
        dom = dom.lower()
        if host == dom or host.endswith("." + dom):
            return True
    return False


def is_recruiting_vendor_host(host: str) -> bool:
    h = (host or "").lower()
    return any(h == sfx or h.endswith("." + sfx) for sfx in RECRUITING_VENDOR_SUFFIXES)


def load_extra_brands(path: Path | None) -> dict[str, dict[str, Any]]:
    """Optional JSON file: { \"acme\": { \"display\": ..., \"domains\": [...] } }."""
    if not path or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}