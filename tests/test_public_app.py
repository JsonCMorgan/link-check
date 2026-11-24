from __future__ import annotations

import pytest

pytest.importorskip("flask")


@pytest.fixture
def web_client():
    from public_app.app import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(web_client):
    r = web_client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_api_check_intact_paradox(web_client):
    r = web_client.post(
        "/api/check",
        json={
            "url": "https://olivia.paradox.ai/apply",
            "claimed_brand": "Intact Financial",
        },
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["verdict"] == "do_not_click"


def test_index_html(web_client):
    r = web_client.get("/")
    assert r.status_code == 200
    assert b"Link Check" in r.data


def test_api_message_mode(web_client):
    r = web_client.post(
        "/api/check",
        json={
            "message": "Intact Financial apply https://olivia.paradox.ai/x",
        },
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["mode"] == "message"
    assert data["worst"]["verdict"] == "do_not_click"