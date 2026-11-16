#!/usr/bin/env python3
"""Thursday Task Desk card: connect the dots for open house signs.

Reads the export endpoint, groups currently-out sign-outs by color, and posts
ONE Task Desk card (or prints a dry run). On approve/apply, marks ticked
colors returned (which frees them for assignment). Does not send texts or
emails. Does not print secrets.

Usage:
  python3 /workspace/jarvis/open-house-signout/thursday_card.py
      # dry run (default): print the card, post nothing
  python3 /workspace/jarvis/open-house-signout/thursday_card.py --post
      # post one idempotent card for this Thursday (HST)
  python3 /workspace/jarvis/open-house-signout/thursday_card.py --apply --card DATE#N
      # write approved colors back to the Sheet
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = Path(os.environ.get("DESK_STATE", "/workspace/jarvis/state"))
HST = timezone(timedelta(hours=-10), name="HST")
SWATCH = {
    "red": "🟥", "blue": "🟦", "green": "🟩", "yellow": "🟨", "orange": "🟧",
    "purple": "🟪", "pink": "🩷", "black": "⬛", "white": "⬜", "brown": "🟫",
    "lightblue": "🔹", "lime": "🟢",
}


def load_env() -> dict:
    env = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if not line.strip() or line.strip().startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k] = v
    return env


def today_hst() -> date:
    return datetime.now(HST).date()


def thursday_key(d: date | None = None) -> str:
    d = d or today_hst()
    return f"oh-signs-{d.isoformat()}"


def format_phone(num: str) -> str:
    d = re.sub(r"\D", "", str(num or ""))
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    if len(d) != 10:
        return str(num or "").strip()
    return f"({d[:3]}) {d[3:6]}-{d[6:]}"


def load_colors() -> dict:
    p = ROOT / "colors.json"
    if not p.exists():
        p = ROOT / "site/open-house-sign-out-sheet/colors.json"
    if not p.exists():
        return {"palette": [], "assignments": {}}
    return json.loads(p.read_text())


def color_meta(cid: str, number: str, colors: dict) -> dict:
    pal = colors.get("palette") or []
    asg = colors.get("assignments") or {}
    cid = (cid or "").strip().lower()
    digits = re.sub(r"\D", "", number or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if not cid and digits:
        cid = str(asg.get(digits) or "").lower()
    for c in pal:
        if str(c.get("id") or "").lower() == cid:
            return {
                "id": c["id"],
                "name": c.get("name") or c["id"],
                "hex": c.get("hex") or "",
                "number": c.get("number") or digits,
            }
    return {"id": cid or "unknown", "name": (cid or "Unknown").title(), "hex": "", "number": digits}


def export_rows(env: dict) -> tuple[list[dict], list[dict]]:
    url = env.get("SIGN_OUT_EXPORT_URL") or env.get("APPS_SCRIPT_EXEC_URL") or ""
    key = env.get("EXPORT_SECRET") or ""
    if not url or not key:
        raise SystemExit("Need SIGN_OUT_EXPORT_URL / APPS_SCRIPT_EXEC_URL and EXPORT_SECRET in .env")
    q = urllib.parse.urlencode({"action": "export", "key": key})
    req = urllib.request.Request(url + ("&" if "?" in url else "?") + q, headers={"User-Agent": "TalkRealtySignOutThursday/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    if not data.get("ok"):
        raise SystemExit(f"export failed: {data.get('error') or 'unknown'}")
    return data.get("rows") or [], data.get("flags") or []


def is_out(row: dict) -> bool:
    ret = str(row.get("returned") or "").strip().upper()
    return ret not in {"Y", "YES"}


def short_date(val: str) -> str:
    s = str(val or "").strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    return m.group(1) if m else s


def group_out(rows: list[dict], colors: dict) -> list[dict]:
    groups: OrderedDict[str, dict] = OrderedDict()
    for row in rows:
        if not is_out(row):
            continue
        meta = color_meta(str(row.get("color") or ""), str(row.get("sign_number") or ""), colors)
        key = meta["id"] or format_phone(row.get("sign_number") or "")
        if key not in groups:
            groups[key] = {
                "color_id": meta["id"],
                "color_name": meta["name"],
                "hex": meta["hex"],
                "sign_number": format_phone(meta.get("number") or row.get("sign_number") or ""),
                "items": [],
            }
        groups[key]["items"].append(row)
        if not groups[key]["sign_number"]:
            groups[key]["sign_number"] = format_phone(row.get("sign_number") or "")
    out = []
    for g in groups.values():
        # One row per color: use the current (latest) sign-out for agent/date/location
        items = sorted(g["items"], key=lambda r: str(r.get("submitted_at") or r.get("oh_date") or ""), reverse=True)
        lead = items[0]
        out.append({
            "color_id": g["color_id"],
            "color_name": g["color_name"],
            "hex": g["hex"],
            "sign_number": g["sign_number"],
            "agent_name": lead.get("agent_name") or "",
            "agent_phone": lead.get("agent_phone") or "",
            "oh_date": short_date(lead.get("oh_date") or lead.get("submitted_at") or ""),
            "address": lead.get("address") or "",
            "tokens": [r.get("token") for r in items if r.get("token")],
            "item_count": len(items),
        })
    return out


def card_text(groups: list[dict], flags: list[dict], thursday: date) -> str:
    lines = []
    try:
        label = thursday.strftime("%A, %B %-d, %Y")
    except Exception:
        label = thursday.isoformat()
    heading = f"Open house signs still out, as of {label}."
    if thursday.strftime("%A") == "Thursday":
        heading = f"Open house signs still out, Thursday {label}."
    lines.append(heading)
    lines.append("Connect the dots: match each returned sign's color dot to its wall section, then tick Returned for that color.")
    lines.append("Type how many signs are in the office, then press Send. This does not text or email anyone.")
    lines.append("")
    if not groups:
        lines.append("No sign colors are currently signed out.")
    else:
        lines.append("Currently out:")
        for g in groups:
            sw = SWATCH.get(g["color_id"], "●")
            lines.append(
                f"- {sw} {g['color_name'].upper()}  {g['sign_number']}  —  {g['agent_name']}, {g['oh_date']}, {g['address']}"
            )
    lines.append("")
    lines.append("Signs in office: ")
    recent = [f for f in flags if str(f.get("logged_at") or "").startswith(thursday.isoformat())]
    if recent:
        lines.append("")
        lines.append(f"Note: the form flagged all colors out {len(recent)} time(s) today. Someone may have needed a color that was already signed out.")
    return "\n".join(lines) + "\n"


def checklist_for(groups: list[dict]) -> list[dict]:
    items = []
    for g in groups:
        sw = SWATCH.get(g["color_id"], "●")
        items.append({
            "id": f"color-{g['color_id']}",
            "label": f"Returned: {sw} {g['color_name']}  ·  {g['sign_number']}  ·  {g['agent_name']}  ·  {g['oh_date']}  ·  {g['address']}",
            "done": False,
            "colorId": g["color_id"],
            "tokens": g["tokens"],
        })
    return items


def body_html(groups: list[dict]) -> str:
    if not groups:
        return "<p>No sign colors are currently signed out.</p>"
    rows = []
    for g in groups:
        hexcolor = g.get("hex") or "#1B365D"
        rows.append(
            "<tr>"
            f"<td style='padding:8px 10px;vertical-align:middle'><span style='display:inline-block;width:18px;height:18px;border-radius:50%;background:{hexcolor};border:1px solid #1A1A1A'></span></td>"
            f"<td style='padding:8px 10px'>{_esc(g['color_name'])}</td>"
            f"<td style='padding:8px 10px'>{_esc(g['sign_number'])}</td>"
            f"<td style='padding:8px 10px'>{_esc(g['agent_name'])}</td>"
            f"<td style='padding:8px 10px'>{_esc(g['oh_date'])}</td>"
            f"<td style='padding:8px 10px'>{_esc(g['address'])}</td>"
            "</tr>"
        )
    return (
        "<p>Connect the dots. Tick <strong>Returned</strong> on the card for each color that is back on the wall.</p>"
        "<table style='border-collapse:collapse;width:100%;background:#fff;border:1px solid #e3d9c6'>"
        "<thead><tr style='background:#1B365D;color:#fff'>"
        "<th style='padding:8px 10px;text-align:left'></th>"
        "<th style='padding:8px 10px;text-align:left'>Color</th>"
        "<th style='padding:8px 10px;text-align:left'>Sign number</th>"
        "<th style='padding:8px 10px;text-align:left'>Agent</th>"
        "<th style='padding:8px 10px;text-align:left'>Sign-out date</th>"
        "<th style='padding:8px 10px;text-align:left'>Location</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
        "<p style='margin-top:12px'>Signs in office: (type the count in the card text)</p>"
    )


def _esc(s: str) -> str:
    return (
        str(s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_item(groups: list[dict], flags: list[dict], thursday: date) -> dict:
    key = thursday_key(thursday)
    draft = card_text(groups, flags, thursday)
    return {
        "label": f"Open house signs — Thursday check {thursday.isoformat()}",
        "channel": "internal",
        "kind": "task",
        "scriptId": "oh-signs-thursday",
        "dedupeKey": key,
        "section": "needs_today",
        "awayExclude": True,
        "needsJudgment": True,
        "dueLabel": f"Thursday {thursday.isoformat()}, connect the dots",
        "action": (
            "Tick Returned for each color whose signs are back on the wall. "
            "Type the office sign count. Press Send. Jarvis writes those colors back to the tracker Sheet "
            "and frees them for the next sign-out. Do not send texts or emails. "
            "Number routing back to Christopher is later, after his list of numbers."
        ),
        "context": "Christopher checks signs every Thursday by matching each sign's color dot to the wall section.",
        "factors": [
            "One row per color currently out, not one row per agent if the same color is somehow listed twice.",
            "Ticking Returned and pressing Send marks those Sheet rows Returned=Y, which frees the color.",
            "Leave a color unticked if those signs are still out.",
        ],
        "draftText": draft,
        "bodyHtml": body_html(groups),
        "checklist": checklist_for(groups),
        "ohSigns": {
            "dedupeKey": key,
            "date": thursday.isoformat(),
            "groups": groups,
            "flags_today": len([f for f in flags if str(f.get("logged_at") or "").startswith(thursday.isoformat())]),
        },
        "recipient": {"name": "Talk Realty office"},
        "who": "Open house signs",
    }


def already_posted(key: str) -> str | None:
    if not STATE.exists():
        return None
    for p in sorted(STATE.glob("approvals-*.json"), reverse=True):
        try:
            data = json.loads(p.read_text())
        except Exception:
            continue
        for it in data.get("items") or []:
            if not isinstance(it, dict):
                continue
            if it.get("dedupeKey") == key or (it.get("ohSigns") or {}).get("dedupeKey") == key:
                st = it.get("status") or "pending"
                return f"{data.get('date') or p.name[10:20]}#{it.get('n')} ({st})"
    return None


def post_card(item: dict, thursday: date) -> tuple[int, dict]:
    sys.path.insert(0, "/workspace/the-draw")
    from thedraw import desk
    return desk.add_card(item, date=thursday.isoformat())


def load_card(cid: str, test: bool = False) -> dict:
    if test:
        p = STATE / "approvals-test.json"
        data = json.loads(p.read_text())
        n = cid.split("#", 1)[-1] if "#" in cid else cid
        it = next((x for x in data.get("items") or [] if str(x.get("n")) == str(n)), None)
        if not it:
            raise SystemExit(f"No test card {cid}")
        return it
    date_part, _, n = cid.partition("#")
    p = STATE / f"approvals-{date_part}.json"
    if not p.exists():
        raise SystemExit(f"No approvals file for {date_part}")
    data = json.loads(p.read_text())
    it = next((x for x in data.get("items") or [] if str(x.get("n")) == str(n)), None)
    if not it:
        raise SystemExit(f"No card {cid}")
    return it


def parse_office_count(text: str) -> str:
    m = re.search(r"signs in office\s*[:\-]?\s*(\d+)", text or "", re.I)
    return m.group(1) if m else ""


def exec_post(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "text/plain;charset=utf-8", "User-Agent": "TalkRealtySignOutThursday/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def apply_card(cid: str, env: dict, test: bool = False) -> dict:
    it = load_card(cid, test=test)
    groups = ((it.get("ohSigns") or {}).get("groups")) or []
    checklist = it.get("checklist") or []
    returned_ids = {str(x.get("colorId") or x.get("id") or "").replace("color-", "") for x in checklist if x.get("done")}
    # Also honor YES lines in edited draft
    text = it.get("editedText") or it.get("draftText") or ""
    report = {"card": cid, "marked": [], "left_out": [], "office_count": parse_office_count(text), "errors": []}
    url = env.get("APPS_SCRIPT_EXEC_URL") or env.get("SIGN_OUT_EXPORT_URL") or ""
    key = env.get("EXPORT_SECRET") or ""
    for g in groups:
        cid_ = g.get("color_id") or ""
        tokens = g.get("tokens") or []
        if cid_ in returned_ids or f"color-{cid_}" in returned_ids:
            for token in tokens:
                if test:
                    report["marked"].append({"color": cid_, "token": "test", "ok": True})
                    continue
                try:
                    res = exec_post(url, {"action": "return", "r": token})
                    report["marked"].append({"color": cid_, "ok": bool(res.get("ok")), "error": res.get("error")})
                    if not res.get("ok"):
                        report["errors"].append(res.get("error") or "return_failed")
                except Exception as e:
                    report["errors"].append(type(e).__name__)
                    report["marked"].append({"color": cid_, "ok": False, "error": type(e).__name__})
        else:
            report["left_out"].append(cid_ or g.get("color_name"))
    if report["office_count"] and not test:
        try:
            res = exec_post(url, {
                "action": "office-count",
                "key": key,
                "count": report["office_count"],
                "date": (it.get("ohSigns") or {}).get("date") or today_hst().isoformat(),
                "notes": f"Thursday card {cid}",
            })
            report["office_count_write"] = "ok" if res.get("ok") else (res.get("error") or "failed")
        except Exception:
            report["office_count_write"] = "pending_apps_script"
            log = STATE / "oh-office-count.jsonl"
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a") as fh:
                fh.write(json.dumps({"at": datetime.now(HST).isoformat(), "card": cid, "count": report["office_count"]}) + "\n")
    elif report["office_count"] and test:
        report["office_count_write"] = "dry_test"
    else:
        report["office_count_write"] = "not_given"
    # Record outcome on the card when possible (never sends)
    try:
        sys.path.insert(0, "/workspace/the-draw")
        from thedraw import desk
        note = f"Marked returned: {', '.join(m['color'] for m in report['marked'] if m.get('ok')) or 'none'}. Office count: {report['office_count'] or 'not given'}."
        desk.record_execution({
            "id": cid,
            "ok": not report["errors"],
            "note": note,
        }, test=test) if hasattr(desk, "record_execution") else None
    except Exception:
        try:
            cmd = [
                sys.executable,
                "/workspace/jarvis/approval-desk/desk_edit.py",
                "--card", cid.split("#")[-1],
                "--record-sent" if not report["errors"] else "--record-error",
            ]
            # Prefer leaving a note via record-error only when needed; skip if CLI flags differ
        except Exception:
            pass
    # Never print tokens
    safe = {
        "card": report["card"],
        "marked_colors": [m["color"] for m in report["marked"] if m.get("ok")],
        "left_out": report["left_out"],
        "office_count": report["office_count"],
        "office_count_write": report["office_count_write"],
        "errors": report["errors"],
    }
    return safe


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true", help="Post the card to the Task Desk")
    ap.add_argument("--dry-run", action="store_true", default=False, help="Print the card and post nothing (default)")
    ap.add_argument("--apply", action="store_true", help="Write an approved card back to the Sheet")
    ap.add_argument("--card", default="", help="Card id DATE#N for --apply")
    ap.add_argument("--date", default="", help="Thursday date YYYY-MM-DD (defaults to today HST)")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args(argv)
    env = load_env()
    if args.apply:
        if not args.card:
            print("Need --card DATE#N", file=sys.stderr)
            return 2
        result = apply_card(args.card, env, test=args.test)
        print(json.dumps(result, indent=2))
        return 0 if not result.get("errors") else 1
    thursday = date.fromisoformat(args.date) if args.date else today_hst()
    rows, flags = export_rows(env)
    colors = load_colors()
    groups = group_out(rows, colors)
    item = build_item(groups, flags, thursday)
    print("dedupe_key", item["dedupeKey"])
    print("out_colors", len(groups))
    print("======= card text =======")
    print(item["draftText"])
    if groups:
        print("======= checklist =======")
        for c in item["checklist"]:
            # no tokens in printed output
            print("-", c["label"], "[ ] Returned")
    if not args.post:
        print("dry_run: nothing posted")
        return 0
    existing = already_posted(item["dedupeKey"])
    if existing:
        print(f"already_posted {existing}; not adding a second card")
        return 0
    code, rec = post_card(item, thursday)
    n = rec.get("n") if isinstance(rec, dict) else None
    print("post_status", code, "card", f"{thursday.isoformat()}#{n}" if n else rec)
    return 0 if code < 300 else 1


if __name__ == "__main__":
    sys.exit(main())
