"""
Public Link Check web app (Option 1).

Run: pip install -e ".[public]" && python public_app/app.py
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Any

from flask import Flask, jsonify, render_template, request

from link_check.analyze import analyze_link
from link_check.message import analyze_message
from link_check.qr_analyze import analyze_qr_bytes

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024

# Simple in-memory rate limit (fine for single-instance public v0.1).
_RATE_WINDOW_SEC = 60
_RATE_MAX = 40
_hits: dict[str, list[float]] = defaultdict(list)


def _client_ip() -> str:
    forwarded = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    return forwarded or (request.remote_addr or "unknown")


def _verify_careers_on(data: dict[str, Any]) -> bool:
    v = data.get("verify_careers")
    if isinstance(v, bool):
        return v
    return str(v or "").lower() in ("1", "true", "yes", "on")


def _rate_ok(ip: str) -> bool:
    now = time.time()
    window = _hits[ip]
    _hits[ip] = [t for t in window if now - t < _RATE_WINDOW_SEC]
    if len(_hits[ip]) >= _RATE_MAX:
        return False
    _hits[ip].append(now)
    return True


def _check_payload(
    data: dict[str, Any],
    *,
    qr_bytes: bytes | None = None,
) -> tuple[dict[str, Any], int]:
    ip = _client_ip()
    if not _rate_ok(ip):
        return {"ok": False, "error": "Too many checks; wait a minute and try again."}, 429

    claimed = (data.get("claimed_brand") or data.get("claimed") or "").strip()
    verify_careers = _verify_careers_on(data)

    if qr_bytes or (data.get("qr_paste") or "").strip():
        return (
            analyze_qr_bytes(
                qr_bytes or b"",
                claimed_brand=claimed,
                pasted_url=(data.get("qr_paste") or "").strip(),
                verify_careers=verify_careers,
            ),
            200,
        )

    message = (data.get("message") or data.get("text") or "").strip()
    if message:
        return analyze_message(message, claimed_brand=claimed, verify_careers=verify_careers), 200

    url = (data.get("url") or "").strip()
    if not url:
        return {"ok": False, "error": "Paste a URL, message, or QR image."}, 400
    return analyze_link(url, claimed_brand=claimed, verify_careers=verify_careers), 200


@app.route("/")
def index():
    """Single-page check UI."""
    return render_template("index.html", site_name="Link Check")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html", site_name="Link Check")


@app.route("/health")
def health():
    return jsonify({"ok": True, "service": "link-check", "offline": True})


@app.route("/api/check", methods=["POST"])
def api_check():
    """JSON body: url, optional claimed_brand."""
    data = request.get_json(silent=True) or {}
    result, status = _check_payload(data)
    return jsonify(result), status


@app.route("/check", methods=["POST"])
def form_check():
    """HTML form post (no JS required)."""
    mode = (request.form.get("mode") or "url").strip().lower()
    qr_bytes: bytes | None = None
    if mode == "qr" and request.files.get("qr_image"):
        qr_bytes = request.files["qr_image"].read() or None

    data = {
        "claimed_brand": request.form.get("claimed_brand") or "",
        "url": request.form.get("url") or "",
        "message": request.form.get("message") or "" if mode == "message" else "",
        "qr_paste": request.form.get("qr_paste") or "" if mode == "qr" else "",
        "verify_careers": request.form.get("verify_careers"),
    }
    result, status = _check_payload(data, qr_bytes=qr_bytes if mode == "qr" else None)
    if request.accept_mimetypes.best == "application/json":
        return jsonify(result), status
    return render_template(
        "index.html",
        site_name="Link Check",
        result=result,
        form_mode=mode,
        form_url=data["url"],
        form_message=data.get("message") or "",
        form_qr_paste=data.get("qr_paste") or "",
        form_claimed=data["claimed_brand"],
        form_verify_careers=_verify_careers_on(data),
    ), status if status != 200 else 200


def main() -> None:
    host = os.environ.get("LINK_CHECK_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", os.environ.get("LINK_CHECK_PORT", "5055")))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()