#!/usr/bin/env python3
"""Static site checks. No deploy, no live Sheet."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
TITLE = "Talk Realty Open House Sign Out Sheet"
WARNING = "Take only the signs from the color section you are given"
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
    assert "warning-key" in page and "take only the signs from the color section you are given" in page.lower()
    assert "Please read before you sign out signs" not in page
    assert "warning-icon" in page and "border-left: 6px solid" in css
    assert "bg-video" in page and "bgVideo" in js
    assert "../assets/bg.mp4" not in js
    assert "prefersReducedMotion" in js and "saveData" in js
    assert "initCardTilt" not in js
    assert "left = 3" not in js and "left: 3" not in js
    assert "action=available" in js
    assert "total = 5" in js
    for field_id in ["agent-name", "agent-phone", "address"]:
        assert field_id in page, field_id
    colors = (ROOT / "site" / "open-house-sign-out-sheet" / "colors.json").read_text()
    assert colors.count('"id"') == 5
    assert "8083787316" in colors
    assert "8086701135" not in colors
    assert "alt_numbers" not in colors
    assert "8084008551" in colors
    assert "8085186893" in colors
    assert "8082011994" in colors
    assert "example, pending Devin confirm" in colors
    assert '"pending": true' in colors  # Orange / fifth line still unconfirmed
    assert 'id="sign-list"' not in page and "Sign numbers" not in page
    assert "sign-list-items" not in page
    assert "confirm-example-note" in page and "confirm-alt" in page
    assert "confirm-example-note" in css and "confirm-alt" in css
    assert "alt_numbers" not in js
    assert "also " not in js
    assert "loadInventory" in js and "exampleLabelDefault" in js
    assert "colors.json" in js
    assert "withInventory" in js
    assert (ROOT / "site" / "assets" / "bg.jpg").exists()
    assert (ROOT / "site" / "assets" / "bg.mp4").exists()
    assert (ROOT / "site" / "assets" / "bg.mp4").stat().st_size < 30 * 1024 * 1024
    assert "sign-typed" not in page
    assert "return-link" not in page
    assert "text you a return" not in page.lower()
    assert "we will also text" not in page.lower()
    assert "Your open house signs are the ones under the" in page
    assert "Your open house signs phone number is" in page
    assert "confirm-number-label" in page and "confirm-number" in page
    assert "confirm-color-name" in page and "confirm-color-name" in js
    assert "font-family: var(--serif)" in css
    assert "clamp(1.9rem, 8vw, 2.6rem)" in css
    assert "font-weight: 600" in css
    assert "Playfair+Display:wght@400;500;600" in page
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
    assert "confirm-reset-link" not in page
    assert "all-out-reset-link" not in page
    # Reveal screen must never show a reset link, even in test mode.
    confirm = page.split('id="confirm-screen"', 1)[1]
    assert "Reset test colors" not in confirm
    assert "confirm-reset" not in confirm
    assert "All open house signs are currently out" in page
    assert "None are available right now. Please check back later." in page
    assert "all-out-overlay" in page and "all-out-overlay" in css
    assert "backdrop-filter: blur(" in css
    assert "formLocked" in js and "setFormLocked" in js
    assert "pointer-events: none" in css
    start = page.find('id="all-out"')
    copy_at = page.find('all-out-copy', start)
    # The overlay is a div wrapping all-out-copy; stop at the form-stage close that follows it.
    end = page.find('id="test-reset-wrap"', start)
    overlay = page[start:end if end > start else start + 600]
    assert "all-out-copy" in overlay and copy_at != -1
    assert "Reset test colors" not in overlay
    assert "all-out-reset" not in overlay
    assert "testMode" in js and "q.get('test')" in js
    assert (ROOT / "site" / "open-house-sign-out-sheet" / "test" / "index.html").exists()
    assert "Christopher Strickland" not in js
    # CSS comment may mention box-shadow; only reject actual properties.
    # Website shadows are requested for card/button depth (not packet PDFs).
    print("site content tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
