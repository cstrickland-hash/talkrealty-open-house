Background media for the sign-out page

  site/assets/bg.mp4         Desktop loop (1920x1080, muted, ~53s).
  site/assets/bg-mobile.mp4  Mobile loop (1280x720), chosen when the
                             viewport is under 768px wide.
  site/assets/bg.jpg         Poster still from an early frame.

SIGN_OUT_CONFIG in site/open-house-sign-out-sheet/config.js points at
these files. The page lazy-loads the video, skips it when the phone
prefers reduced motion or save-data (poster still shows), and covers
the viewport. The form card stays static (no tilt or parallax).

Source footage (Webpae.mov) is not in this folder or the public repo.
