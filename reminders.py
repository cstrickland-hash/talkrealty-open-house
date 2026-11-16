#!/usr/bin/env python3
"""UNUSED (Christopher t4840u / t4849u, Nov 15 2026).

Return reminder texts are cancelled. Do not schedule the 6:30 PM or 12 PM
(noon) text jobs, and do not send texts from this file. Thursday sign checks
now go through thursday_card.py and the Task Desk.

The functions below are left in place only as unused reference.
"""
from __future__ import annotations

import argparse, json, os, re, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
HERE = Path(__file__).resolve().parent
FUB_URL = "https://api.followupboss.com/v1/people"


def load_env(path: Path | None = None) -> None:
    env_path = path or HERE / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def digits(s: str) -> str:
    d = re.sub(r"[^0-9]", "", s or "")
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    return d


def parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    value = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value[:19] if "T" in value else value[:19], fmt)
            return dt.replace(tzinfo=HST)
        except ValueError:
            continue
    return None


def parse_date(value: str):
    dt = parse_dt(value)
    return dt.date() if dt else None


def first_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return "there"
    return name.split()[0]


def now_hst(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(HST)
    if now.tzinfo is None:
        return now.replace(tzinfo=HST)
    return now.astimezone(HST)


def within_send_window(now: datetime) -> bool:
    # 8:00 AM up to but not including 9:00 PM HST
    t = now.time()
    return t.hour >= 8 and t.hour < 21


def fetch_rows(url: str, secret: str) -> list[dict]:
    if not url:
        raise SystemExit("SIGN_OUT_EXPORT_URL is missing")
    if not secret:
        raise SystemExit("EXPORT_SECRET is missing")
    sep = "&" if "?" in url else "?"
    full = f"{url}{sep}action=export&key={urllib.parse.quote(secret)}"
    req = urllib.request.Request(full, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    data = json.loads(body)
    if not data.get("ok"):
        raise SystemExit("export failed")
    return list(data.get("rows") or [])


def load_rows(args) -> list[dict]:
    if args.input:
        raw = json.loads(Path(args.input).read_text())
        if isinstance(raw, dict) and "rows" in raw:
            return list(raw["rows"])
        if isinstance(raw, list):
            return raw
        raise SystemExit("input JSON must be a list or {rows: [...]}")
    url = args.url or os.environ.get("SIGN_OUT_EXPORT_URL") or ""
    secret = os.environ.get("EXPORT_SECRET") or ""
    return fetch_rows(url, secret)


def reminder_due(row: dict, job: str, now: datetime) -> tuple[bool, str]:
    if str(row.get("returned") or "").upper().startswith("Y"):
        return False, "already_returned"
    oh = parse_date(row.get("oh_date") or "")
    if not oh:
        return False, "missing_oh_date"
    today = now.date()
    planned = parse_date(row.get("planned_return_date") or "")
    if planned and planned >= today:
        return False, "planned_return_in_future"
    last = parse_dt(row.get("last_reminder_at") or "")
    if last and (now - last) < timedelta(hours=24):
        return False, "reminded_in_last_24h"

    if job == "evening":
        if oh != today:
            return False, "not_today"
        return True, "evening_today"

    # noon / daily
    # If a planned return date has passed, treat that as the trigger date.
    if planned and planned < today:
        return True, "planned_return_passed"
    if oh >= today:
        return False, "oh_not_yet_yesterday"
    return True, "noon_overdue"


def message_for(row: dict, base: str) -> str:
    token = row.get("token") or ""
    link = base.rstrip("/") + "/return.html?r=" + token
    name = first_name(row.get("agent_name") or "")
    return (
        f"Aloha {name}, this is Christopher at Talk Realty. "
        f"When you have a chance, tap here to mark your open house signs as returned "
        f"or tell us the day you will bring them back: {link}"
    )


def fub_lookup(phone: str) -> dict:
    """Return {fub_person_id} or {needs_fub_contact: True}. Never prints the key."""
    key = os.environ.get("FUB_API_KEY") or ""
    d = digits(phone)
    if not key or not d:
        return {"fub_person_id": None, "needs_fub_contact": True, "fub_lookup": "skipped" if not key else "no_phone"}
    import base64

    def get(params: dict):
        q = urllib.parse.urlencode(params)
        req = urllib.request.Request(
            f"{FUB_URL}?{q}",
            headers={
                "Authorization": "Basic " + base64.b64encode((key + ":").encode()).decode(),
                "X-System": "Jarvis",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())

    people = []
    try:
        data = get({"phone": d, "limit": "5"})
        people = data.get("people") or []
    except Exception:
        people = []
    if not people:
        try:
            data = get({"query": d, "limit": "5"})
            people = data.get("people") or []
        except Exception:
            people = []

    wanted = d[-10:] if len(d) >= 10 else d
    matches = []
    for p in people:
        for ph in p.get("phones") or []:
            val = digits(str(ph.get("value") or ph.get("number") or ""))
            if val and (val == wanted or val.endswith(wanted) or wanted.endswith(val[-10:] if len(val) >= 10 else val)):
                matches.append(p)
                break
    if len(matches) == 1:
        return {"fub_person_id": matches[0].get("id"), "needs_fub_contact": False, "fub_lookup": "matched"}
    if len(matches) > 1:
        return {"fub_person_id": None, "needs_fub_contact": True, "fub_lookup": "ambiguous"}
    return {"fub_person_id": None, "needs_fub_contact": True, "fub_lookup": "no_match"}


def build_job(rows: list[dict], job: str, now: datetime, base: str, skip_fub: bool) -> dict:
    if not within_send_window(now):
        return {
            "job": job,
            "now": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "skipped": "outside_send_window",
            "texts": [],
            "note": "No texts after 9 PM HST (or before 8 AM HST).",
        }
    texts = []
    skipped = []
    for row in rows:
        ok, reason = reminder_due(row, job, now)
        if not ok:
            skipped.append({"token": row.get("token"), "reason": reason})
            continue
        item = {
            "token": row.get("token"),
            "agent_name": row.get("agent_name"),
            "phone": row.get("agent_phone"),
            "message": message_for(row, base),
            "reason": reason,
        }
        if skip_fub:
            item["fub_person_id"] = row.get("fub_person_id") or None
            item["needs_fub_contact"] = not bool(item["fub_person_id"])
            item["fub_lookup"] = "skipped"
        else:
            lookup = fub_lookup(row.get("agent_phone") or "")
            item.update(lookup)
        texts.append(item)
    return {
        "job": job,
        "now": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "count": len(texts),
        "texts": texts,
        "skipped": skipped,
        "note": "This list is a draft only. FUB cannot send texts by API. Sending is a FUB UI browser step and costs more than a free API call.",
    }


def post_mark_sent(url: str, secret: str, token: str, sent_at: str, fub_id) -> dict:
    payload = json.dumps({
        "action": "mark-sent",
        "key": secret,
        "token": token,
        "sent_at": sent_at,
        "fub_person_id": fub_id or "",
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "text/plain;charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def mark_sent_local(path: Path, token: str, sent_at: str, fub_id) -> dict:
    raw = json.loads(path.read_text())
    rows = raw["rows"] if isinstance(raw, dict) and "rows" in raw else raw
    found = None
    for row in rows:
        if str(row.get("token")) == token:
            prev = int(row.get("reminder_count") or 0)
            row["last_reminder_at"] = sent_at
            row["reminder_count"] = prev + 1
            if fub_id:
                row["fub_person_id"] = fub_id
            found = row
            break
    if not found:
        return {"ok": False, "error": "not_found"}
    if isinstance(raw, dict) and "rows" in raw:
        raw["rows"] = rows
        path.write_text(json.dumps(raw, indent=2))
    else:
        path.write_text(json.dumps(rows, indent=2))
    return {"ok": True, "row": found}


def main(argv=None) -> int:
    load_env()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("job", choices=["evening", "noon", "daily", "mark-sent"])
    p.add_argument("--input", help="Local JSON fixture (does not touch the live Sheet)")
    p.add_argument("--url", help="Apps Script /exec URL (or SIGN_OUT_EXPORT_URL)")
    p.add_argument("--base-url", dest="base_url", help="Public return-page base, .../open-house-sign-out-sheet")
    p.add_argument("--now", help="Override now, 'YYYY-MM-DD HH:MM' HST")
    p.add_argument("--token", help="For mark-sent")
    p.add_argument("--sent-at", dest="sent_at", help="For mark-sent, HST timestamp")
    p.add_argument("--fub-id", dest="fub_id", help="For mark-sent")
    p.add_argument("--skip-fub", action="store_true", help="Do not call the FUB API")
    p.add_argument("--out", help="Write JSON to this path")
    args = p.parse_args(argv)

    now = now_hst(parse_dt(args.now) if args.now else None)
    base = (
        args.base_url
        or os.environ.get("SIGN_OUT_PUBLIC_BASE")
        or "https://YOUR-SERVICE.onrender.com/open-house-sign-out-sheet"
    )

    if args.job == "mark-sent":
        if not args.token:
            print("mark-sent needs --token", file=sys.stderr)
            return 2
        sent_at = args.sent_at or now.strftime("%Y-%m-%d %H:%M:%S")
        if args.input:
            result = mark_sent_local(Path(args.input), args.token, sent_at, args.fub_id)
        else:
            url = args.url or os.environ.get("SIGN_OUT_EXPORT_URL") or ""
            secret = os.environ.get("EXPORT_SECRET") or ""
            if not url or not secret:
                print("mark-sent against the live sheet needs SIGN_OUT_EXPORT_URL and EXPORT_SECRET", file=sys.stderr)
                return 2
            result = post_mark_sent(url, secret, args.token, sent_at, args.fub_id)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    job = "noon" if args.job == "daily" else args.job
    rows = load_rows(args)
    result = build_job(rows, job, now, base, skip_fub=args.skip_fub or bool(args.input))
    # For --input tests, skip live FUB by default (already skip_fub if --input)
    text = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
