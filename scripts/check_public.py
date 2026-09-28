"""Redacted checks for common accidental disclosure in this repository."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

CHECKS = {
    "credential signature": re.compile(
        r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
        r"sk-[A-Za-z0-9_-]{24,}|nfp_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})"
    ),
    "private key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "credential assignment": re.compile(
        r"(?im)\b(?:NETLIFY_TOKEN|(?:API[_-]?KEY)|PASSWORD|SECRET)\s*="
        r"\s*(?!\$|<|\{|['\"]\s*['\"])[^\s\"'`]{8,}"
    ),
    "personal filesystem path": re.compile(
        r"(?:[A-Za-z]:[\\/]Users[\\/][^\s\"']+|/Users/[^/\s]+|/home/[^/\s]+)", re.I
    ),
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "production publishing identifier": re.compile(
        r"taylor-weekly-brief(?:\.netlify\.app)?|G-[A-Z0-9]{10,}", re.I
    ),
    "identified employer marker": re.compile(r"玉山"),
    "sensitive customer field": re.compile(
        r"\b(?:client|customer)[_-](?:name|email|phone|account|record|data|id)\b", re.I
    ),
    "advisory watchlist label": re.compile(r"美股推薦追蹤|推薦個股|推薦股票|recommended stocks?", re.I),
    "explicit trade signal": re.compile(r"\b(?:buy|sell)\s+(?:rating|signal|recommendation|target)\b", re.I),
}


def repository_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path == SELF:
            continue
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        yield path


def main():
    findings = []
    for path in repository_files():
        relative = path.relative_to(ROOT).as_posix()
        if path.name == ".env" or path.name.startswith(".env.") or path.suffix.lower() in {".pem", ".key"}:
            findings.append((relative, "private configuration or key file"))
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            findings.append((relative, "unreviewed image or screenshot"))
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        # The neutral disclaimer intentionally explains that the watchlist is not advice.
        text = text.replace(
            "Watchlist items are included for market observation and workflow demonstration only "
            "and do not constitute investment recommendations.",
            "",
        )
        for category, pattern in CHECKS.items():
            if pattern.search(text) or (category == "personal filesystem path" and pattern.search(relative)):
                findings.append((relative, category))

    if findings:
        print("Public-content check failed (paths and categories only):")
        for path, category in findings:
            print(f"- {path}: {category}")
        return 1
    print("Public-content check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
