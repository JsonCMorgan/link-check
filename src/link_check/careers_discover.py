"""Discover careers URLs on an employer's own domains (no search engines)."""

from __future__ import annotations

import re
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

from link_check.brands import host_matches_brand

_MAX_DISCOVER_FETCH = 5
_CAREER_HREF = re.compile(
    r"""href\s*=\s*["']([^"']+)["']""",
    re.I,
)
_CAREER_PATH = re.compile(r"(career|jobs?|join|talent|recruit|opportunit)", re.I)


def _root_urls_for_domain(domain: str) -> list[str]:
    d = domain.lower().strip().lstrip(".")
    if not d:
        return []
    return [f"https://{d}/", f"https://www.{d}/"]


def _guess_careers_urls(domain: str) -> list[str]:
    d = domain.lower().strip()
    return [
        f"https://careers.{d}/",
        f"https://jobs.{d}/",
        f"https://{d}/careers",
        f"https://{d}/careers/",
        f"https://www.{d}/careers",
        f"https://www.{d}/careers/",
    ]


def _normalize_discovered(base: str, href: str) -> str | None:
    href = (href or "").strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    try:
        full = urljoin(base, href)
        parsed = urlparse(full)
    except ValueError:
        return None
    if parsed.scheme not in ("http", "https"):
        return None
    if not parsed.netloc:
        return None
    path = parsed.path or "/"
    if not _CAREER_PATH.search(path) and not _CAREER_PATH.search(parsed.netloc):
        return None
    return f"{parsed.scheme}://{parsed.netloc}{path}".rstrip("/") + ("/" if path.endswith("/") else "")


def _links_from_html(page_url: str, html: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for m in _CAREER_HREF.finditer(html or ""):
        norm = _normalize_discovered(page_url, m.group(1))
        if not norm or norm in seen:
            continue
        seen.add(norm)
        found.append(norm)
    return found


def discover_careers_urls(
    brand: dict[str, Any],
    fetch: Callable[[str], tuple[int, bytes, str]],
    *,
    max_fetch: int = _MAX_DISCOVER_FETCH,
) -> dict[str, Any]:
    """
    Find careers URLs by fetching homepages and common paths on brand-owned domains.

    Never calls third-party search APIs.
    """
    domains = [str(d).lower() for d in (brand.get("domains") or ()) if str(d).strip()]
    if not domains:
        return {"urls": [], "steps": [], "plain": "No domains configured for this employer."}

    candidates: list[str] = []
    for dom in domains[:4]:
        candidates.extend(_guess_careers_urls(dom))
        candidates.extend(_root_urls_for_domain(dom))

    seen_c: set[str] = set()
    queue: list[str] = []
    for u in candidates:
        if u not in seen_c:
            seen_c.add(u)
            queue.append(u)

    steps: list[dict[str, Any]] = []
    found: list[str] = []
    seen_found: set[str] = set()
    fetches = 0

    for url in queue:
        if fetches >= max_fetch:
            steps.append({"url": url, "skipped": "max_fetch_cap"})
            break
        if not host_matches_brand(urlparse(url).netloc.lower(), brand):
            continue
        fetches += 1
        try:
            status, body, final = fetch(url)
            text = body.decode("utf-8", errors="replace")
            steps.append({"url": url, "final_url": final, "status": status, "kind": "fetch"})
            if status >= 400:
                continue
            for link in _links_from_html(final, text):
                if host_matches_brand(urlparse(link).netloc.lower(), brand) and link not in seen_found:
                    seen_found.add(link)
                    found.append(link)
            if _CAREER_PATH.search(urlparse(final).path) or _CAREER_PATH.search(
                urlparse(final).netloc
            ):
                if final not in seen_found:
                    seen_found.add(final)
                    found.append(final)
        except OSError as exc:
            steps.append({"url": url, "error": str(exc)[:160]})

    primary = domains[0]
    plain = (
        f"Discovered {len(found)} careers-related URL(s) on {brand.get('display') or primary}'s domains."
        if found
        else f"Could not discover careers URLs on {brand.get('display') or primary}'s sites in {fetches} fetch(es)."
    )

    return {
        "urls": found,
        "steps": steps,
        "fetches_used": fetches,
        "plain": plain,
        "discover": True,
    }