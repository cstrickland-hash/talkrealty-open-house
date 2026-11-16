Background media slot (not shown until enabled)

  site/assets/bg.jpg   Optional poster still.
  site/assets/bg.mp4   Muted looping clip.

The live page currently uses a calm navy fallback (no video). When Christopher
provides a replacement clip, put it at site/assets/bg.mp4 (and optional bg.jpg),
then set SIGN_OUT_CONFIG.bgVideo to "../assets/bg.mp4" in
site/open-house-sign-out-sheet/config.js. The page will lazy-load it, skip it
when the phone prefers reduced motion or save-data, and cover the viewport.
