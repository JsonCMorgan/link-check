from __future__ import annotations

import os

from link_check.brands import reload_brand_registry
from link_check.web_search import web_search_careers


def test_web_search_ranks_brand_careers_url(monkeypatch):
    reload_brand_registry()
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    monkeypatch.delenv("SEARXNG_URL", raising=False)
    monkeypatch.setenv("SERPER_API_KEY", "test-key")

    def fake_search(query: str):
        assert "Intact" in query
        return (
            "serper",
            [
                {
                    "url": "https://careers.intactfc.com/jobs",
                    "title": "Intact Financial Careers",
                    "snippet": "Apply for jobs at Intact",
                },
                {
                    "url": "https://www.indeed.com/intact",
                    "title": "Indeed",
                    "snippet": "jobs",
                },
            ],
        )

    from link_check import web_search as ws

    monkeypatch.setattr(ws, "_run_search", lambda q: fake_search(q))

    r = web_search_careers("Intact Financial")
    assert r["ok"]
    assert "https://careers.intactfc.com/jobs" in r["careers_candidates"]


def test_web_search_no_provider():
    reload_brand_registry()
    old = os.environ.pop("SERPER_API_KEY", None)
    os.environ.pop("BRAVE_SEARCH_API_KEY", None)
    os.environ.pop("SEARXNG_URL", None)
    try:
        r = web_search_careers("Intact Financial")
        assert r["skipped"]
        assert "SERPER_API_KEY" in r["plain"]
    finally:
        if old:
            os.environ["SERPER_API_KEY"] = old