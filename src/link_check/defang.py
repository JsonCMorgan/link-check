"""Defang URLs for safe sharing."""

from __future__ import annotations

from urllib.parse import urlparse


def defang_url(url: str) -> str:
    """Hxxp scheme and bracketed dots."""
    u = (url or "").strip()
    u = u.replace("http://", "hxxp://").replace("https://", "hxxps://")
    return u.replace(".", "[.]")


def parse_host(url: str) -> str:
    """Return lowercase host from URL or empty."""
    raw = (url or "").strip()
    if not raw:
        return ""
    if "://" not in raw and not raw.startswith("//"):
        raw = "https://" + raw
    try:
        parsed = urlparse(raw)
    except ValueError:
        return ""
    host = (parsed.netloc or "").lower()
    if "@" in host:
        host = host.split("@", 1)[-1]
    if ":" in host:
        host = host.rsplit(":", 1)[0]
    return host.lstrip(".")