"""Decode URL payloads from QR code images (offline, local file only)."""

from __future__ import annotations

from typing import Any


def decode_qr_image(image_bytes: bytes) -> dict[str, Any]:
    """
    Return {ok, payloads: [str], error?} using OpenCV QR detector (no network).
    """
    if not image_bytes:
        return {"ok": False, "error": "No image data.", "payloads": []}

    try:
        import cv2
        import numpy as np
    except ImportError:
        return {
            "ok": False,
            "error": "QR decoding is not installed. Run: pip install -e \".[public]\" (includes OpenCV).",
            "payloads": [],
        }

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {"ok": False, "error": "Could not read that image file.", "payloads": []}

    detector = cv2.QRCodeDetector()
    payloads: list[str] = []

    if hasattr(detector, "detectAndDecodeMulti"):
        ok, decoded, _points, _ = detector.detectAndDecodeMulti(img)
        if ok and decoded is not None:
            for item in decoded:
                text = (item or "").strip()
                if text:
                    payloads.append(text)
    if not payloads:
        text, _points, _ = detector.detectAndDecode(img)
        text = (text or "").strip()
        if text:
            payloads.append(text)

    if not payloads:
        return {
            "ok": False,
            "error": "No QR code found in that image. Try a clearer photo or paste the URL below.",
            "payloads": [],
        }

    seen: set[str] = set()
    unique: list[str] = []
    for p in payloads:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    return {"ok": True, "payloads": unique}