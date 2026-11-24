"""Analyze decoded QR payload(s) as links or message text."""

from __future__ import annotations

from typing import Any

from link_check.analyze import analyze_link
from link_check.message import analyze_message


def analyze_qr_payloads(
    payloads: list[str],
    *,
    claimed_brand: str = "",
    verify_careers: bool = False,
) -> dict[str, Any]:
    """Run message or link analysis on each QR decode result."""
    if not payloads:
        return {"ok": False, "error": "Nothing to analyze."}

    combined = "\n".join(payloads)
    if any("http" in p.lower() or "www." in p.lower() for p in payloads):
        return analyze_message(combined, claimed_brand=claimed_brand, verify_careers=verify_careers)

    primary = payloads[0].strip()
    if primary.lower().startswith("http") or "://" in primary:
        row = analyze_link(primary, claimed_brand=claimed_brand, verify_careers=verify_careers)
        return {**row, "mode": "qr", "qr_payloads": payloads}

    return {
        "ok": False,
        "error": (
            "QR content is not a recognizable link. "
            "Paste the URL manually on Single URL, or use a photo of a URL QR."
        ),
        "qr_payloads": payloads,
    }


def analyze_qr_bytes(
    image_bytes: bytes,
    *,
    claimed_brand: str = "",
    pasted_url: str = "",
    verify_careers: bool = False,
) -> dict[str, Any]:
    """Decode image then analyze; optional pasted_url if decode fails."""
    from link_check.qr_decode import decode_qr_image

    decoded = decode_qr_image(image_bytes)
    payloads = list(decoded.get("payloads") or [])
    if pasted_url.strip():
        payloads.append(pasted_url.strip())

    if not payloads:
        return {**decoded, "ok": False}

    result = analyze_qr_payloads(payloads, claimed_brand=claimed_brand, verify_careers=verify_careers)
    result["mode"] = "qr"
    result["qr_decode"] = decoded
    result["qr_payloads"] = payloads
    return result