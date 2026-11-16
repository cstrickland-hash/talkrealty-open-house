#!/usr/bin/env python3
"""One sign-out QR poster plus printable color wall labels. Never prints secrets."""
from __future__ import annotations

import argparse
import json
import sys
from io import BytesIO
from pathlib import Path

import segno
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdfcanvas

ROOT = Path(__file__).resolve().parent
DEFAULT_URL = "https://talkrealty-open-house.onrender.com/open-house-sign-out-sheet/"
NAVY = (27, 54, 93)
INK = (26, 26, 26)
CREAM = (251, 247, 240)
GOLD = (196, 163, 90)


def load_colors(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    pal = data.get("palette") or []
    asg = data.get("assignments") or {}
    inv = []
    for c in pal:
        item = dict(c)
        num = "".join(ch for ch in str(item.get("number") or "") if ch.isdigit())
        if len(num) == 11 and num.startswith("1"):
            num = num[1:]
        if len(num) != 10:
            for raw, cid in asg.items():
                digits = "".join(ch for ch in str(raw) if ch.isdigit())
                if len(digits) == 11 and digits.startswith("1"):
                    digits = digits[1:]
                if digits and str(cid).lower() == str(item.get("id") or "").lower():
                    num = digits
                    break
        item["number"] = num if len(num) == 10 else ""
        inv.append(item)
    return inv


def format_phone(num: str) -> str:
    d = "".join(ch for ch in str(num or "") if ch.isdigit())
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    if len(d) != 10:
        return ""
    return f"({d[:3]}) {d[3:6]}-{d[6:]}"


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = str(h or "").lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        return (27, 54, 93)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def qr_image(url: str, scale: int = 16) -> Image.Image:
    bio = BytesIO()
    segno.make(url, error="h").save(bio, kind="png", scale=scale, border=2, dark=NAVY, light="white")
    bio.seek(0)
    return Image.open(bio).convert("RGB")


def poster_png(url: str, out: Path, *, test: bool = False) -> Path:
    """Simple printable poster: title, large QR, short instruction."""
    w, h = 2550, 3300  # 8.5x11 at 300 dpi
    img = Image.new("RGB", (w, h), CREAM)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w, 36], fill=NAVY)
    draw.rectangle([0, 36, w, 52], fill=GOLD)
    title = font(96, True)
    sub = font(48, False)
    cap = font(56, True)
    foot = font(36, False)
    t = "Talk Realty Open House Sign Out Sheet"
    bbox = draw.textbbox((0, 0), t, font=title)
    draw.text(((w - (bbox[2] - bbox[0])) / 2, 180), t, font=title, fill=NAVY)
    s = "Scan to open the TEST sign-out page" if test else "Scan to sign out open house signs"
    bbox = draw.textbbox((0, 0), s, font=sub)
    draw.text(((w - (bbox[2] - bbox[0])) / 2, 340), s, font=sub, fill=INK)
    if test:
        badge = font(64, True)
        label = "TEST MODE"
        bb = draw.textbbox((0, 0), label, font=badge)
        bw, bh = bb[2] - bb[0], bb[3] - bb[1]
        bx = (w - bw) // 2
        by = 420
        pad_x, pad_y = 36, 16
        draw.rectangle([bx - pad_x, by - pad_y, bx + bw + pad_x, by + bh + pad_y], fill=GOLD, outline=NAVY, width=6)
        draw.text((bx, by), label, font=badge, fill=NAVY)
    qr = qr_image(url, scale=28)
    # Make the QR large and centered
    target = 1600 if test else 1700
    qr = qr.resize((target, target), Image.Resampling.NEAREST)
    x, y = (w - target) // 2, (620 if test else 520)
    img.paste(qr, (x, y))
    inst = "Open the camera on your phone and scan this code"
    bbox = draw.textbbox((0, 0), inst, font=cap)
    draw.text(((w - (bbox[2] - bbox[0])) / 2, y + target + 80), inst, font=cap, fill=NAVY)
    bbox = draw.textbbox((0, 0), "Talk Realty  ·  Honolulu, Hawaii", font=foot)
    draw.text(((w - (bbox[2] - bbox[0])) / 2, h - 180), "Talk Realty  ·  Honolulu, Hawaii", font=foot, fill=(92, 87, 79))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def poster_pdf(png: Path, out: Path, url: str) -> Path:
    c = pdfcanvas.Canvas(str(out), pagesize=letter)
    pw, ph = letter
    c.setFillColorRGB(251 / 255, 247 / 255, 240 / 255)
    c.rect(0, 0, pw, ph, fill=1, stroke=0)
    c.drawImage(ImageReader(str(png)), 0, 0, width=pw, height=ph, preserveAspectRatio=True, anchor="c")
    c.setTitle("Talk Realty Open House Sign Out Sheet")
    c.showPage()
    c.save()
    return out


def wall_label_png(color: dict, out: Path) -> Path:
    w, h = 2550, 3300
    rgb = hex_rgb(color.get("hex"))
    text_rgb = hex_rgb(color.get("text") or "#FFFFFF")
    border = hex_rgb(color.get("border") or color.get("hex"))
    img = Image.new("RGB", (w, h), CREAM)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w, 36], fill=NAVY)
    draw.rectangle([0, 36, w, 52], fill=GOLD)
    # Large color dot
    margin = 280
    diameter = min(w, h) - 2 * margin - 700
    cx, cy = w // 2, 420 + diameter // 2
    box = [cx - diameter // 2, cy - diameter // 2, cx + diameter // 2, cy + diameter // 2]
    draw.ellipse(box, fill=rgb, outline=border, width=18)
    name = str(color.get("name") or color.get("id") or "").upper()
    nf = font(140, True)
    bbox = draw.textbbox((0, 0), name, font=nf)
    draw.text(((w - (bbox[2] - bbox[0])) / 2, cy + diameter // 2 + 80), name, font=nf, fill=NAVY)
    number = format_phone(color.get("number") or "")
    if number:
        pf = font(110, True)
        bbox = draw.textbbox((0, 0), number, font=pf)
        draw.text(((w - (bbox[2] - bbox[0])) / 2, cy + diameter // 2 + 260), number, font=pf, fill=INK)
    else:
        pf = font(48, False)
        t = "Sign number coming soon"
        bbox = draw.textbbox((0, 0), t, font=pf)
        draw.text(((w - (bbox[2] - bbox[0])) / 2, cy + diameter // 2 + 280), t, font=pf, fill=(92, 87, 79))
    foot = font(36, False)
    t = "Talk Realty  ·  Honolulu, Hawaii"
    bbox = draw.textbbox((0, 0), t, font=foot)
    draw.text(((w - (bbox[2] - bbox[0])) / 2, h - 180), t, font=foot, fill=(92, 87, 79))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def labels_pdf(pngs: list[Path], out: Path) -> Path:
    c = pdfcanvas.Canvas(str(out), pagesize=letter)
    pw, ph = letter
    for p in pngs:
        c.setFillColorRGB(251 / 255, 247 / 255, 240 / 255)
        c.rect(0, 0, pw, ph, fill=1, stroke=0)
        c.drawImage(ImageReader(str(p)), 0, 0, width=pw, height=ph, preserveAspectRatio=True, anchor="c")
        c.showPage()
    c.save()
    return out


def decode_qr(path: Path) -> str:
    import cv2
    import numpy as np
    from PIL import Image as PImage
    img = PImage.open(path).convert("RGB")
    arr = np.array(img)
    det = cv2.QRCodeDetector()
    data, _, _ = det.detectAndDecode(arr)
    if not data:
        w, h = img.size
        crop = img.crop((int(w * 0.12), int(h * 0.15), int(w * 0.88), int(h * 0.80)))
        data, _, _ = det.detectAndDecode(np.array(crop))
    if not data:
        raise SystemExit(f"QR did not decode: {path}")
    return data


def public_url() -> str:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if not line.strip() or line.strip().startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k in {"SIGN_OUT_PUBLIC_BASE", "STATIC_URL"} and v.strip():
                url = v.strip()
                if not url.endswith("/"):
                    url += "/"
                if not url.rstrip("/").endswith("open-house-sign-out-sheet"):
                    url = url.rstrip("/") + "/open-house-sign-out-sheet/"
                return url
    return DEFAULT_URL


def test_url(base: str) -> str:
    base = (base or public_url()).strip()
    if not base.endswith("/"):
        base += "/"
    if "test=1" not in base:
        joiner = "&" if "?" in base else "?"
        base = base + joiner + "test=1"
    return base


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="")
    ap.add_argument("--outdir", default=str(ROOT / "qr"))
    ap.add_argument("--colors", default=str(ROOT / "colors.json"))
    ap.add_argument("--test", action="store_true", help="Generate the TEST MODE poster only")
    args = ap.parse_args(argv)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if args.test:
        url = test_url(args.url or public_url())
        sample = ROOT / "talkrealty-open-house-sign-out-TEST-qr.png"
        poster_png(url, sample, test=True)
        pdf = ROOT / "talkrealty-open-house-sign-out-TEST-qr.pdf"
        poster_pdf(sample, pdf, url)
        decoded = decode_qr(sample)
        if decoded.rstrip("/") != url.rstrip("/"):
            raise SystemExit(f"QR decoded to {decoded!r}, expected {url!r}")
        print("url", url)
        print("sample_png", sample)
        print("sample_pdf", pdf)
        print("decoded_ok", decoded)
        return 0
    url = (args.url or public_url()).strip()
    if not url.endswith("/"):
        url += "/"
    poster = outdir / "talkrealty-open-house-sign-out-sheet-qr-poster.png"
    poster_png(url, poster)
    pdf = outdir / "talkrealty-open-house-sign-out-sheet-qr-poster.pdf"
    poster_pdf(poster, pdf, url)
    decoded = decode_qr(poster)
    if decoded.rstrip("/") != url.rstrip("/"):
        raise SystemExit(f"QR decoded to {decoded!r}, expected {url!r}")
    inv = load_colors(Path(args.colors))
    labels_dir = outdir / "wall-labels"
    pngs = []
    for c in inv:
        cid = c.get("id") or "color"
        pngs.append(wall_label_png(c, labels_dir / f"{cid}.png"))
    labels_pdf(pngs, outdir / "wall-labels.pdf")
    print("url", url)
    print("poster_png", poster)
    print("poster_pdf", pdf)
    print("wall_labels_pdf", outdir / "wall-labels.pdf")
    print("wall_label_count", len(pngs))
    print("decoded_ok", decoded)
    return 0


if __name__ == "__main__":
    sys.exit(main())
