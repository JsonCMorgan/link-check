"""Brand-to-domain registry from JSON defaults and optional packs."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

# Third-party hiring vendors; mismatch alone is not proof of fraud.
RECRUITING_VENDOR_SUFFIXES = (
    "paradox.ai",
    "myworkdayjobs.com",
    "greenhouse.io",
    "lever.co",
    "icims.com",
    "taleo.net",
    "smartrecruiters.com",
)


def _data_dir() -> Path:
    return Path(__file__).resolve().parent / "data"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _load_pack_file(path: Path) -> dict[str, Any]:
    raw = _read_json(path)
    if "brands" in raw and isinstance(raw["brands"], dict):
        return raw["brands"]
    return raw


def _default_pack_ids() -> list[str]:
    env = (os.environ.get("LINK_CHECK_PACKS") or "").strip()
    if env:
        if env.lower() == "none":
            return []
        return [p.strip() for p in env.split(",") if p.strip()]
    packs_dir = _data_dir() / "packs"
    if not packs_dir.is_dir():
        return []
    return sorted(p.stem for p in packs_dir.glob("*.json"))


@lru_cache(maxsize=1)
def brand_registry() -> dict[str, dict[str, Any]]:
    """Merge brands_default.json and enabled packs (all packs in data/packs/ by default)."""
    merged: dict[str, dict[str, Any]] = {}

    default_path = _data_dir() / "brands_default.json"
    merged.update(_read_json(default_path))

    for pack_id in _default_pack_ids():
        pack_path = _data_dir() / "packs" / f"{pack_id}.json"
        if pack_path.is_file():
            merged.update(_load_pack_file(pack_path))

    return merged


def reload_brand_registry() -> None:
    """Clear cache after data file edits (tests)."""
    brand_registry.cache_clear()


def _normalize_brand_key(name: str) -> str:
    n = (name or "").lower()
    for ch in ".,'\"()-":
        n = n.replace(ch, " ")
    return " ".join(n.split())


def resolve_brand(claimed: str) -> dict[str, Any] | None:
    """Match claimed company text to a brand record."""
    if not claimed:
        return None
    key = _normalize_brand_key(claimed)
    brands = brand_registry()
    for bid, row in brands.items():
        disp = _normalize_brand_key(row.get("display") or "")
        if bid in key or key in disp or disp in key or key in bid:
            return {**row, "id": bid}
    return None


def host_matches_brand(host: str, brand: dict[str, Any]) -> bool:
    """True if host is the brand domain or a subdomain of it."""
    if not host or not brand:
        return False
    for dom in brand.get("domains") or ():
        dom = str(dom).lower()
        if host == dom or host.endswith("." + dom):
            return True
    return False


def is_recruiting_vendor_host(host: str) -> bool:
    h = (host or "").lower()
    return any(h == sfx or h.endswith("." + sfx) for sfx in RECRUITING_VENDOR_SUFFIXES)


def list_pack_names() -> list[str]:
    """Pack ids currently enabled."""
    return _default_pack_ids()