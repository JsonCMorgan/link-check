from __future__ import annotations

from link_check.brands import reload_brand_registry, resolve_brand
from link_check.careers_discover import discover_careers_urls


def test_discover_finds_careers_href():
    reload_brand_registry()
    brand = resolve_brand("Intact Financial")
    assert brand

    def fake_fetch(url: str):
        if "intact.ca" in url and "/careers" not in url:
            html = b'<a href="https://careers.intactfc.com/jobs">Careers</a>'
            return 200, html, url
        return 200, b"paradox talent", url

    r = discover_careers_urls(brand, fake_fetch)
    assert "https://careers.intactfc.com/jobs" in r["urls"] or any(
        "careers" in u for u in r["urls"]
    )