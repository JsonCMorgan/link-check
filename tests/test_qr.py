from __future__ import annotations

import io

import pytest

from link_check.qr_analyze import analyze_qr_bytes, analyze_qr_payloads


def test_qr_payloads_analyze_as_message():
    r = analyze_qr_payloads(
        ["https://olivia.paradox.ai/x"],
        claimed_brand="Intact Financial",
    )
    assert r["ok"]
    assert r["results"][0]["verdict"] == "do_not_click"


def test_qr_paste_without_image():
    r = analyze_qr_bytes(b"", pasted_url="https://olivia.paradox.ai/x", claimed_brand="Intact Financial")
    assert r["ok"]
    assert r["mode"] == "qr"


def test_qr_image_decode():
    qrcode = pytest.importorskip("qrcode")
    pytest.importorskip("cv2", reason="opencv in public extra")
    buf = io.BytesIO()
    qrcode.make("https://test.example/qr-path").save(buf, format="PNG")
    r = analyze_qr_bytes(buf.getvalue())
    assert r["ok"]
    assert any("test.example" in p for p in (r.get("qr_payloads") or []))