"""Stage 2: web search for official careers links (opt-in, env API keys)."""

from __future__ import annotations

import json
import os
import re
import ssl
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from link_check.brands import host_matches_brand, resolve_brand

_CAREER_HINT = re.compile(r"career|jobs?|hiring|talent|join us|apply", re.I)
_TIMEOUT = 12


def _provider_name() -> str | None:
    if (os.environ.get("SERPER_API_KEY") or "").strip():
        return "serper"
    if (os.environ.get("BRAVE_SEARCH_API_KEY") or "").strip():
        return "brave"
    if (os.environ.get("SEARXNG_URL") or "").strip():
        return "searxng"
    return None


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, headers={**headers, "Content-Type": "application/json"}, method="POST")
    ctx = ssl.create_default_context()
    with urlopen(req, timeout=_TIMEOUT, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    req = Request(url, headers=headers, method="GET")
    ctx = ssl.create_default_context()
    with urlopen(req, timeout=_TIMEOUT, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _build_query(display: str, domains: list[str]) -> str:
    dom = domains[0] if domains else ""
    if dom:
        return f'{display} official careers site OR site:{dom} careers'
    return f"{display} official careers jobs apply"


def _normalize_hits(raw_links: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in raw_links:
        link = (row.get("url") or "").strip()
        if not link or not link.startswith("http"):
            continue
        key = link.lower().rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "url": link,
                "title": (row.get("title") or "")[:200],
                "snippet": (row.get("snippet") or "")[:300],
            }
        )
    return out


def _search_serper(query: str) -> list[dict[str, str]]:
    key = (os.environ.get("SERPER_API_KEY") or "").strip()
    if not key:
        return []
    data = _post_json(
        "https://google.serper.dev/search",
        {"q": query, "num": 10, "gl": "ca", "hl": "en"},
        {"X-API-KEY": key},
    )
    organic = data.get("organic") or []
    return [
        {"url": o.get("link", ""), "title": o.get("title", ""), "snippet": o.get("snippet", "")}
        for o in organic
        if isinstance(o, dict)
    ]


def _search_brave(query: str) -> list[dict[str, str]]:
    key = (os.environ.get("BRAVE_SEARCH_API_KEY") or "").strip()
    if not key:
        return []
    from urllib.parse import quote

    url = (
        "https://api.search.brave.com/res/v1/web/search?"
        f"q={quote(query)}&count=10&country=CA&search_lang=en"
    )
    data = _get_json(
        url,
        {
            "Accept": "application/json",
            "X-Subscription-Token": key,
        },
    )
    web = data.get("web") or {}
    results = web.get("results") or []
    return [
        {
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "snippet": r.get("description", ""),
        }
        for r in results
        if isinstance(r, dict)
    ]


def _search_searxng(query: str) -> list[dict[str, str]]:
    base = (os.environ.get("SEARXNG_URL") or "").strip().rstrip("/")
    if not base:
        return []
    from urllib.parse import quote

    url = f"{base}/search?q={quote(query)}&format=json"
    data = _get_json(url, {"Accept": "application/json"})
    results = data.get("results") or []
    return [
        {"url": r.get("url", ""), "title": r.get("title", ""), "snippet": r.get("content", "")}
        for r in results
        if isinstance(r, dict)
    ]


def _run_search(query: str) -> tuple[str | None, list[dict[str, str]]]:
    provider = _provider_name()
    if provider == "serper":
        return provider, _search_serper(query)
    if provider == "brave":
        return provider, _search_brave(query)
    if provider == "searxng":
        return provider, _search_searxng(query)
    return None, []


def _score_hit(hit: dict[str, str], brand: dict[str, Any] | None) -> int:
    url = hit.get("url") or ""
    title = hit.get("title") or ""
    snippet = hit.get("snippet") or ""
    blob = f"{url} {title} {snippet}"
    score = 0
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return -99
    if brand and host_matches_brand(host, brand):
        score += 50
    if _CAREER_HINT.search(blob):
        score += 25
    if brand:
        disp = (brand.get("display") or "").lower()
        if disp and disp.split()[0] in blob.lower():
            score += 10
    if any(bad in host for bad in ("linkedin.com", "indeed.com", "glassdoor.com", "facebook.com")):
        score -= 15
    return score


def web_search_careers(
    claimed_brand: str,
    *,
    search_fn: Callable[[str], tuple[str | None, list[dict[str, str]]]] | None = None,
) -> dict[str, Any]:
    """
    Search the web for official careers URLs. Requires SERPER_API_KEY, BRAVE_SEARCH_API_KEY, or SEARXNG_URL.
    """
    claimed = (claimed_brand or "").strip()
    if not claimed:
        return {
            "ok": False,
            "skipped": True,
            "reason": "no_company_name",
            "plain": "Enter a company name to run web search.",
        }

    brand = resolve_brand(claimed)
    domains = [str(d) for d in (brand.get("domains") or ())] if brand else []
    display = (brand.get("display") if brand else None) or claimed
    query = _build_query(display, domains)

    provider = _provider_name()
    if not provider:
        return {
            "ok": False,
            "skipped": True,
            "reason": "no_search_provider",
            "plain": (
                "Web search is not configured. Set SERPER_API_KEY (2,500 free queries at serper.dev), "
                "BRAVE_SEARCH_API_KEY (~1,000/month free at brave.com/search/api), or SEARXNG_URL for self-hosted search."
            ),
            "help_url": "https://github.com/JsonCMorgan/link-check/blob/main/docs/WEB_SEARCH_SETUP.md",
        }

    do_search = search_fn or _run_search
    try:
        used_provider, raw_hits = do_search(query)
    except OSError as exc:
        return {
            "ok": False,
            "error": str(exc)[:200],
            "plain": f"Web search failed ({provider}). Try again later.",
            "provider": provider,
            "query": query,
        }

    hits = _normalize_hits(raw_hits)
    ranked: list[dict[str, Any]] = []
    for h in hits:
        ranked.append({**h, "score": _score_hit(h, brand)})

    ranked.sort(key=lambda x: x.get("score", 0), reverse=True)
    careers_candidates: list[str] = []
    suggestions: list[dict[str, Any]] = []

    for row in ranked[:8]:
        url = row["url"]
        host = urlparse(url).netloc.lower()
        on_brand = bool(brand and host_matches_brand(host, brand))
        careerish = bool(_CAREER_HINT.search(f"{url} {row.get('title')} {row.get('snippet')}"))
        suggestions.append({**row, "on_brand_domain": on_brand, "career_hint": careerish})
        if on_brand and careerish and url not in careers_candidates:
            careers_candidates.append(url)
        elif on_brand and url not in careers_candidates and len(careers_candidates) < 3:
            careers_candidates.append(url)

    plain = (
        f"Web search ({used_provider or provider}) for «{query}» returned {len(hits)} result(s). "
        f"Top on-brand careers candidate(s): {', '.join(careers_candidates[:3]) or 'none ranked yet'}."
    )

    return {
        "ok": True,
        "provider": used_provider or provider,
        "query": query,
        "hits": suggestions,
        "careers_candidates": careers_candidates,
        "plain": plain,
        "third_party": used_provider in ("serper", "brave"),
        "internet": True,
    }