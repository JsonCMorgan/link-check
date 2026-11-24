"""Analyze a URL for brand mismatch and basic phishing heuristics (offline)."""

from __future__ import annotations

import re
from typing import Any

from link_check.brands import (
    host_matches_brand,
    is_recruiting_vendor_host,
    resolve_brand,
)
from link_check.defang import defang_url, parse_host

_SUSPICIOUS_TLDS = ("zip", "mov", "xyz", "top", "cam", "rest")
_IP_IN_URL = re.compile(r"https?://\d{1,3}(?:\.\d{1,3}){3}", re.I)


def _risk_level(signals: list[str], verdict: str) -> str:
    if verdict in ("high_risk", "do_not_click"):
        return "high"
    if "brand_mismatch" in signals or "recruiting_vendor_not_brand" in signals:
        return "elevated"
    if signals:
        return "caution"
    return "low"


def analyze_link(url: str, *, claimed_brand: str = "") -> dict[str, Any]:
    """
    Return structured triage: host, defanged URL, signals, plain summary.

    Does not fetch the URL and does not call the internet.
    """
    raw = (url or "").strip()
    if not raw:
        return {"ok": False, "error": "Paste a URL to check."}

    host = parse_host(raw)
    if not host:
        return {"ok": False, "error": "Could not parse a host from that URL."}

    signals: list[str] = []
    notes: list[str] = []
    verdict = "review"

    if "@" in raw:
        signals.append("url_userinfo")
        notes.append("The URL contains @ before the host, a common credential-phish pattern.")

    if _IP_IN_URL.search(raw):
        signals.append("ip_literal")
        notes.append("The link uses a numeric IP instead of a normal domain name.")

    if any(host.endswith("." + tld) for tld in _SUSPICIOUS_TLDS):
        signals.append("suspicious_tld")
        notes.append("The domain uses a TLD that is common in abuse campaigns.")

    brand = resolve_brand(claimed_brand)
    brand_section: dict[str, Any] = {
        "claimed": claimed_brand or "",
        "matched_brand": brand.get("display") if brand else None,
    }

    if brand and not host_matches_brand(host, brand):
        signals.append("brand_mismatch")
        allowed = ", ".join(brand.get("domains") or ())
        notes.append(
            f"You said this is about {brand.get('display')}, but the link host is {host}, "
            f"not {brand.get('display')}'s usual domains (examples: {allowed})."
        )
        if is_recruiting_vendor_host(host):
            signals.append("recruiting_vendor_not_brand")
            notes.append(
                f"{host} is a third-party hiring vendor. Some real employers use it, but scammers "
                "borrow the same story. Open the company's official careers site yourself; do not trust this SMS link."
            )
        verdict = "do_not_click"

    elif claimed_brand and not brand:
        signals.append("unknown_brand_claim")
        notes.append(
            "We do not have a domain list for that company name yet. "
            "Compare the host to the company's official website before you click."
        )
        verdict = "caution"

    if not signals:
        verdict = "low_risk_heuristics"
        notes.append(
            "Offline checks did not flag obvious tricks. This is not a malware scan. "
            "When in doubt, type the official site yourself."
        )

    plain = _plain_summary(verdict, host, brand, signals, notes)

    return {
        "ok": True,
        "url": raw,
        "host": host,
        "defanged": defang_url(raw),
        "verdict": verdict,
        "risk_level": _risk_level(signals, verdict),
        "signals": signals,
        "notes": notes,
        "brand": brand_section,
        "plain_summary": plain,
        "offline": True,
    }


def _plain_summary(
    verdict: str,
    host: str,
    brand: dict[str, Any] | None,
    signals: list[str],
    notes: list[str],
) -> str:
    if verdict == "do_not_click" and brand:
        return (
            f"Stop. The link goes to {host}, not {brand.get('display')}'s own site. "
            "Verify jobs or offers on the company's official website without using this link."
        )
    if "recruiting_vendor_not_brand" in signals:
        return (
            f"The link uses hiring software at {host}. That can be legitimate, but the message "
            "did not match the company's primary domains. Verify on the official careers page."
        )
    if notes:
        return notes[0]
    return f"Host is {host}. No offline red flags; still avoid clicking if the message feels wrong."