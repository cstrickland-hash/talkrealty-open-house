#!/usr/bin/env python3
"""Static site checks. No deploy, no live Sheet."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
TITLE = "Talk Realty Open House Sign Out Sheet"
WARNING = "only signs that share that same phone number, no other ones"
BANNED = ["C Strickland", "Christopher Strickland", "cstrickland"]

SITE_FILES = [
    ROOT / "site" / "index.html",
    ROOT / "site" / "open-house-sign-out-sheet" / "index.html",
    ROOT / "site" / "open-house-sign-out-sheet" / "app.js",
    ROOT / "site" / "open-house-sign-out-sheet" / "styles.css",
]


def main():
    assert not (ROOT / "site" / "open-house-sign-out-sheet" / "return.html").exists(), "return.html should be off the public site"
    for path in SITE_FILES:
        text = path.read_text()
        if path.suffix == ".html":
            for bad in BANNED:
                if bad.lower() in text.lower():
                    raise SystemExit(f"{path} contains banned name {bad!r}")
        if "box-shadow:" in text or "drop-shadow(" in text or "filter: drop-shadow" in text:
            raise SystemExit(f"{path} uses a shadow")
    page = (ROOT / "site" / "open-house-sign-out-sheet" / "index.html").read_text()
    js = (ROOT / "site" / "open-house-sign-out-sheet" / "app.js").read_text()
    css = (ROOT / "site" / "open-house-sign-out-sheet" / "styles.css").read_text()
    assert TITLE in page
    assert WARNING in page
    for field_id in ["agent-name", "agent-phone", "address"]:
        assert field_id in page, field_id
    assert "sign-typed" not in page
    assert "return-link" not in page
    assert "text you a return" not in page.lower()
    assert "we will also text" not in page.lower()
    assert "Go to the" in js and "section of the wall" in js
    assert "prefers-reduced-motion" in js and "prefers-reduced-motion" in css
    assert "confirm-screen" in page and "confirm-screen" in css
    assert "localStorage" in js
    assert "Christopher Strickland" not in js
    print("site content tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
