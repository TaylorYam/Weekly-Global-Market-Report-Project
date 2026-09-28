"""Validate the reviewed, fixed historical snapshot without fetching market data."""

from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "examples" / "historical" / "20260914.html"
# UTF-8 text with normalized line endings; updating this requires a reviewed edit.
EXPECTED_SHA256 = "d0d038c8f090846eb2670ae90038f7c83527922369fc7f3f7cc9b5095cf9f11c"


class PassiveHTML(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "iframe", "object", "embed", "link", "base"}:
            raise ValueError("Active or external document resource found")
        for name, value in attrs:
            if name.startswith("on") or name == "src":
                raise ValueError("Active attribute or fetched resource found")
            if name == "href" and not (value or "").startswith("https://"):
                raise ValueError("Unexpected reference protocol")
            if name == "style" and re.search(r"url\s*\(", value or "", re.I):
                raise ValueError("External style resource found")


def main():
    if not SNAPSHOT.is_file() or SNAPSHOT.stat().st_size == 0:
        raise ValueError("Historical snapshot missing or empty")
    text = SNAPSHOT.read_text(encoding="utf-8")
    required = (
        "Historical Example — September 14, 2026",
        "Originally produced as part of a recurring market-information workflow.",
        "Presented here as a portfolio example.",
        "For informational and educational purposes only.",
        "Not investment advice.",
        "2026年9月14日",
        "Market Watchlist",
    )
    if any(marker not in text for marker in required):
        raise ValueError("Historical date, banner or disclaimer missing")
    forbidden = r"<\s*script\b|G-[A-Z0-9]{10,}|netlify[.]app|googletagmanager|google-analytics|\{\{[^}]+\}\}"
    if re.search(forbidden, text, re.I):
        raise ValueError("Script, tracking, publishing endpoint or placeholder found")
    PassiveHTML().feed(text)
    if sha256(text.encode("utf-8")).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Fixed snapshot changed; inspect and document edits before updating its checksum")
    print("Historical snapshot checks passed.")


if __name__ == "__main__":
    main()
