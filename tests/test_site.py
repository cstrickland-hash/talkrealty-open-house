#!/usr/bin/env python3
"""Static/Apps Script HTML checks. No deploy, no live Sheet."""
from pathlib import Path
import sys, re

ROOT = Path(__file__).resolve().parent.parent
TITLE = "Talk Realty Open House Sign Out Sheet"
WARNING = "Please make sure you sign out the right phone number, and take only signs that share that same phone number, no other ones."
BANNED = ["C Strickland", "Christopher Strickland", "cstrickland"]

SITE_FILES = [
    ROOT / "site" / "index.html",
    ROOT / "site" / "open-house-sign-out-sheet" / "index.html",
    ROOT / "site" / "open-house-sign-out-sheet" / "return.html",
    ROOT / "site" / "open-house-sign-out-sheet" / "app.js",
    ROOT / "site" / "open-house-sign-out-sheet" / "styles.css",
    ROOT / "Index.html",
    ROOT / "Return.html",
]


def main():
    for path in SITE_FILES:
        text = path.read_text()
        if path.suffix in {".html"} or path.name == "app.js":
            for bad in BANNED:
                if bad.lower() in text.lower() and path.suffix == ".html":
                    raise SystemExit(f"{path} contains banned name {bad!r}")
                if bad in text and path.suffix == ".html":
                    raise SystemExit(f"{path} contains banned name {bad!r}")
        if "box-shadow:" in text or "drop-shadow(" in text or "filter: drop-shadow" in text:
            raise SystemExit(f"{path} uses a shadow")
    for path in [
        ROOT / "site" / "open-house-sign-out-sheet" / "index.html",
        ROOT / "Index.html",
    ]:
        text = path.read_text()
        assert TITLE in text, path
        assert WARNING in text, path
        for field_id in ["sign-select", "sign-typed", "num-signs", "agent-name", "agent-phone", "address", "oh-date", "oh-end"]:
            assert field_id in text, (path, field_id)
        assert 'value="17:00"' in text
    ret = (ROOT / "site" / "open-house-sign-out-sheet" / "return.html").read_text()
    assert "I returned the signs" in ret
    assert "plan-date" in ret
    assert TITLE in ret
    # Code.gs setTitle
    gs = (ROOT / "Code.gs").read_text()
    assert "setTitle(TITLE)" in gs or 'setTitle(\'' + TITLE in gs or "setTitle(TITLE)" in gs
    assert TITLE in gs
    assert "C Strickland" not in gs and "Christopher Strickland" not in gs
    css = (ROOT / "site" / "open-house-sign-out-sheet" / "styles.css").read_text()
    assert "box-shadow:" not in css
    print("site content tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
