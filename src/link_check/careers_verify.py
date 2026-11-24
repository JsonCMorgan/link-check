"""Optional fetch of an employer's official careers page (never the suspicious link)."""

from __future__ import annotations

import re
import ssl
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from link_check.brands import careers_page_urls, host_matches_brand, resolve_brand
from link_check.careers_discover import discover_careers_urls

_MAX_BYTES = 512_000
_TIMEOUT_SEC = 10
_MAX_VERIFY_PAGES = 4
_USER_AGENT = "LinkCheck/0.2 careers-verify (+https://github.com/JsonCMorgan/link-check)"

_VENDOR_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("paradox", re.compile(r"paradox\.ai|paradox", re.I)),
    ("olivia", re.compile(r"\bolivia\b", re.I)),
    ("workday", re.compile(r"myworkdayjobs\.com|workday", re.I)),
    ("greenhouse", re.compile(r"greenhouse\.io|greenhouse", re.I)),
    ("lever", re.compile(r"lever\.co|\blever\b", re.I)),
    ("icims", re.compile(r"icims\.com", re.I)),
)


def _default_fetch(url: str) -> tuple[int, bytes, str]:
    """GET url; return (status, body, final_url)."""
    req = Request(url, headers={"User-Agent": _USER_AGENT, "Accept": "text/html"})
    ctx = ssl.create_default_context()
    with urlopen(req, timeout=_TIMEOUT_SEC, context=ctx) as resp:
        status = int(getattr(resp, "status", 200) or 200)
        final = resp.geturl() or url
        chunks: list[bytes] = []
        total = 0
        while True:
            block = resp.read(65536)
            if not block:
                break
            total += len(block)
            if total > _MAX_BYTES:
                chunks.append(block[: max(0, _MAX_BYTES - (total - len(block)))])
                break
            chunks.append(block)
        return status, b"".join(chunks), final


def _url_allowed_for_brand(url: str, brand: dict[str, Any]) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.netloc or "").lower().split("@")[-1]
    if ":" in host:
        host = host.rsplit(":", 1)[0]
    return bool(host) and host_matches_brand(host, brand)


def _detect_vendors(html: str) -> list[str]:
    found: list[str] = []
    for name, pat in _VENDOR_PATTERNS:
        if pat.search(html):
            found.append(name)
    return found


def _vendor_for_host(link_host: str) -> str | None:
    h = (link_host or "").lower()
    if "paradox" in h:
        return "paradox"
    if "workday" in h:
        return "workday"
    if "greenhouse" in h:
        return "greenhouse"
    if "lever" in h:
        return "lever"
    if "icims" in h:
        return "icims"
    return None


def verify_brand_careers(
    claimed_brand: str,
    *,
    link_host: str = "",
    fetch: Callable[[str], tuple[int, bytes, str]] | None = None,
    discover: bool = True,
) -> dict[str, Any]:
    """
    Fetch configured careers URLs for the brand and scan HTML for hiring vendors.

    Never fetches the user-supplied suspicious URL.
    """
    brand = resolve_brand(claimed_brand)
    if not brand:
        return {
            "ok": False,
            "skipped": True,
            "reason": "no_brand_match",
            "plain": "Add a company name we recognize to enable careers-page check.",
        }

    do_fetch = fetch or _default_fetch
    configured = careers_page_urls(brand)
    discovery: dict[str, Any] | None = None
    discovered_urls: list[str] = []

    if discover:
        discovery = discover_careers_urls(brand, do_fetch)
        discovered_urls = list(discovery.get("urls") or [])

    urls: list[str] = []
    seen: set[str] = set()
    for u in configured + discovered_urls:
        if u not in seen:
            seen.add(u)
            urls.append(u)

    url_source = "config"
    if configured and discovered_urls:
        url_source = "config_and_discovered"
    elif discovered_urls:
        url_source = "discovered"

    if not urls:
        plain = f"No careers URLs found for {brand.get('display')}."
        if discovery:
            plain = discovery.get("plain") or plain
        return {
            "ok": False,
            "skipped": True,
            "reason": "no_careers_urls",
            "plain": plain,
            "discovery": discovery,
            "internet": True,
        }
    pages: list[dict[str, Any]] = []
    all_vendors: set[str] = set()

    for url in urls[:_MAX_VERIFY_PAGES]:
        if not _url_allowed_for_brand(url, brand):
            pages.append({"url": url, "error": "blocked_url_not_on_brand_domains"})
            continue
        try:
            status, body, final = do_fetch(url)
            text = body.decode("utf-8", errors="replace")
            vendors = _detect_vendors(text)
            for v in vendors:
                all_vendors.add(v)
            pages.append(
                {
                    "url": url,
                    "final_url": final,
                    "status": status,
                    "vendors_mentioned": vendors,
                }
            )
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            pages.append({"url": url, "error": str(exc)[:200]})

    link_vendor = _vendor_for_host(link_host)
    matches: bool | None = None
    if link_vendor and all_vendors:
        matches = link_vendor in all_vendors or (
            link_vendor == "paradox" and "olivia" in all_vendors
        )

    display = brand.get("display") or claimed_brand
    if not all_vendors:
        plain = (
            f"Fetched {display}'s careers page but did not see common hiring-vendor names in the HTML. "
            "That does not prove your link is fake; pages load widgets dynamically sometimes."
        )
    elif matches is True:
        plain = (
            f"{display}'s official careers page mentions {', '.join(sorted(all_vendors))}, "
            f"which aligns with a {link_host} link. Scammers reuse the same vendors. "
            "Still start from the careers site you typed yourself, not this message."
        )
    elif matches is False:
        plain = (
            f"{display}'s careers page mentions {', '.join(sorted(all_vendors))}, "
            f"but that does not match host {link_host}. Treat the message link as suspicious."
        )
    else:
        plain = (
            f"{display}'s careers page mentions {', '.join(sorted(all_vendors))}. "
            "Compare that to your link host. This does not prove this exact URL is authentic."
        )

    if discovery and discovered_urls:
        plain = (
            f"{plain} Live discovery found: {', '.join(discovered_urls[:3])}"
            + (" …" if len(discovered_urls) > 3 else "")
            + "."
        )

    return {
        "ok": True,
        "brand": display,
        "pages": pages,
        "careers_urls_used": urls,
        "url_source": url_source,
        "discovered_urls": discovered_urls,
        "configured_urls": configured,
        "discovery": discovery,
        "vendors_on_careers_site": sorted(all_vendors),
        "link_host": link_host,
        "vendor_matches_link_host": matches,
        "plain": plain,
        "opt_in": True,
        "internet": True,
    }