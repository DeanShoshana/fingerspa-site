#!/usr/bin/env python3
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
HTML_FILES = ("index.html", "privacy.html", "terms.html", "support.html", "404.html")


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.has_title = False
        self.has_viewport = False
        self.has_noindex = False
        self.lang: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.lang = values.get("lang")
        elif tag == "title":
            self.has_title = True
        elif tag == "meta" and values.get("name") == "viewport":
            self.has_viewport = True
        elif tag == "meta" and values.get("name") == "robots":
            self.has_noindex = "noindex" in (values.get("content") or "")
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"site validation failed: {message}")


for relative_path in HTML_FILES:
    path = ROOT / relative_path
    require(path.is_file(), f"missing {relative_path}")
    text = path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(text)

    require(parser.lang == "en", f"{relative_path} must declare English")
    require(parser.has_title, f"{relative_path} needs a title")
    require(parser.has_viewport, f"{relative_path} needs a viewport meta tag")
    require(parser.has_noindex, f"{relative_path} must remain noindex before launch")
    require("<script" not in text.lower(), f"{relative_path} must not load tracking or scripts")

    for link in parser.links:
        parsed = urlparse(link)
        require(not parsed.scheme and not parsed.netloc, f"{relative_path} has external link: {link}")
        target = link.split("#", 1)[0]
        if target:
            require((path.parent / target).is_file(), f"{relative_path} has broken link: {link}")

privacy = (ROOT / "privacy.html").read_text(encoding="utf-8")
terms = (ROOT / "terms.html").read_text(encoding="utf-8")
support = (ROOT / "support.html").read_text(encoding="utf-8")

for phrase in ("no account", "third-party tracking", "Keychain", "iCloud Key-Value Store", "StoreKit"):
    require(phrase.lower() in privacy.lower(), f"privacy.html is missing required topic: {phrase}")

for phrase in ("not a medical service or treatment", "Stop using it immediately", "one-time", "not a subscription"):
    require(phrase.lower() in terms.lower(), f"terms.html is missing required topic: {phrase}")

for phrase in ("supported physical iPhone", "Stop the session immediately", "Restore Purchase", "Support email pending"):
    require(phrase.lower() in support.lower(), f"support.html is missing required topic: {phrase}")

robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
require("Disallow: /" in robots, "robots.txt must prevent pre-release indexing")

print("FingerSpa site validation passed.")
