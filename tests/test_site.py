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
        if "drop-shadow(" in text or "filter: drop-shadow" in text:
            raise SystemExit(f"{path} uses a drop-shadow filter")
    page = (ROOT / "site" / "open-house-sign-out-sheet" / "index.html").read_text()
    js = (ROOT / "site" / "open-house-sign-out-sheet" / "app.js").read_text()
    css = (ROOT / "site" / "open-house-sign-out-sheet" / "styles.css").read_text()
    assert TITLE in page
    assert WARNING in page
    assert "Talk Realty" in page and "Open House Sign Out" in page
    assert "wordmark" in page
    assert "sign-sets-left" in page and "Sign sets left" in page
    assert "sign-sets-left" in css
    assert "warning-key" in page and "take only the signs from the color section you are given" in page
    assert "warning-icon" in page and "border-left: 6px solid" in css
    assert "bg-video" in page and "assets/bg.mp4" in js and "assets/bg.jpg" in page
    assert "prefersReducedMotion" in js and "saveData" in js
    assert "initCardTilt" in js
    for field_id in ["agent-name", "agent-phone", "address"]:
        assert field_id in page, field_id
    colors = (ROOT / "site" / "open-house-sign-out-sheet" / "colors.json").read_text()
    assert colors.count('"id"') == 5
    assert "8083787316" in colors and '"pending": true' in colors
    assert (ROOT / "site" / "assets" / "bg.jpg").exists()
    assert (ROOT / "site" / "assets" / "bg.mp4").exists()
    assert (ROOT / "site" / "assets" / "bg.mp4").stat().st_size < 2 * 1024 * 1024
    assert "sign-typed" not in page
    assert "return-link" not in page
    assert "text you a return" not in page.lower()
    assert "we will also text" not in page.lower()
    assert "Your open house signs are the ones under the" in page
    assert "confirm-color-name" in page and "confirm-color-name" in js
    assert ("Playfair+Display" in page or "Playfair Display" in page) and "Playfair Display" in css
    assert ("Inter+Tight" in page or "Inter Tight" in page) and "Inter Tight" in css
    assert "display=swap" in page and 'rel="preload"' in page
    assert "letter-spacing: 0.12em" in css
    assert "text-transform: uppercase" in css
    assert "#161b2e" in css
    assert "prefers-reduced-motion" in js and "prefers-reduced-motion" in css
    assert "confirm-screen" in page and "confirm-screen" in css
    assert "transition: opacity 1.8s ease" in css
    assert "localStorage" in js
    assert "TEST MODE" in page and "test-badge" in page
    assert "test-reset" in js and "test-reset" in page
    assert "testMode" in js and "q.get('test')" in js
    assert (ROOT / "site" / "open-house-sign-out-sheet" / "test" / "index.html").exists()
    assert "Christopher Strickland" not in js
    # CSS comment may mention box-shadow; only reject actual properties.
    # Website shadows are requested for card/button depth (not packet PDFs).
    print("site content tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
