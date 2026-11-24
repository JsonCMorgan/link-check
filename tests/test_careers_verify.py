from __future__ import annotations

from link_check.analyze import analyze_link
from link_check.brands import reload_brand_registry
from link_check.careers_verify import verify_brand_careers


def test_verify_blocked_url_not_on_brand(monkeypatch):
    reload_brand_registry()

    def fake_fetch(url: str):
        return 200, b"<html>paradox olivia talent assistant</html>", url

    r = verify_brand_careers(
        "Intact Financial",
        link_host="olivia.paradox.ai",
        fetch=fake_fetch,
    )
    assert r["ok"]
    assert "paradox" in r["vendors_on_careers_site"]
    assert r["vendor_matches_link_host"] is True


def test_analyze_link_opt_in_attaches_careers(monkeypatch):
    reload_brand_registry()

    def fake_fetch(url: str):
        return 200, b"Intact Talent Assistant powered by paradox", url

    monkeypatch.setattr("link_check.careers_verify._default_fetch", fake_fetch)
    r = analyze_link(
        "https://olivia.paradox.ai/apply",
        claimed_brand="Intact Financial",
        verify_careers=True,
    )
    assert r["careers_verify"]["ok"]
    assert "paradox" in r["careers_verify"]["vendors_on_careers_site"]