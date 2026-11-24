"""CLI: python -m link_check \"https://...\" --claimed \"Intact Financial\""""

from __future__ import annotations

import argparse
import json
import sys

from link_check.analyze import analyze_link


def _format_text(data: dict) -> str:
    if not data.get("ok"):
        return f"Error: {data.get('error', 'unknown')}"

    lines = [
        f"Host: {data.get('host')}",
        f"Defanged: {data.get('defanged')}",
        f"Risk: {data.get('risk_level')} · Verdict: {data.get('verdict')}",
        "",
        data.get("plain_summary") or "",
    ]
    for n in data.get("notes") or []:
        if n != data.get("plain_summary"):
            lines.append(f"• {n}")
    if data.get("signals"):
        lines.extend(["", f"Signals: {', '.join(data['signals'])}"])
    lines.append("")
    lines.append("(Offline check only — no URL was fetched, no cloud lookup.)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a link offline before you click (brand mismatch + heuristics)."
    )
    parser.add_argument("url", help="URL or host to check")
    parser.add_argument(
        "--claimed",
        default="",
        help="Who the message claims to be (e.g. 'Intact Financial')",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args(argv)

    result = analyze_link(args.url, claimed_brand=args.claimed)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(_format_text(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())