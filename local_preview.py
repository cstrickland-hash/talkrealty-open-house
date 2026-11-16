#!/usr/bin/env python3
"""Local preview for Talk Realty Open House Sign Out Sheet. Does not touch the live Sheet.

  python3 local_preview.py
  # then open http://127.0.0.1:8765/open-house-sign-out-sheet/
"""
from __future__ import annotations

import json, uuid
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DATA = ROOT / "tests" / "sample" / "local-store.json"
NUMBERS = ROOT / "tests" / "sample" / "sign-numbers.json"


def now_hst():
    return datetime.now(HST).strftime("%Y-%m-%d %H:%M:%S")


def load_store():
    if DATA.is_file():
        return json.loads(DATA.read_text())
    return {"rows": []}


def save_store(store):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(store, indent=2) + "\n")


def numbers():
    if NUMBERS.is_file():
        raw = json.loads(NUMBERS.read_text())
        return raw if isinstance(raw, list) else raw.get("numbers") or []
    return []


def find(store, token):
    for row in store["rows"]:
        if row.get("token") == token:
            return row
    return None


def handle(action, data):
    store = load_store()
    action = (action or data.get("action") or "").lower()
    if action == "health":
        return {"ok": True, "service": "Talk Realty Open House Sign Out Sheet"}
    if action == "numbers":
        return {"ok": True, "numbers": numbers()}
    if action == "export":
        return {"ok": True, "rows": store["rows"]}
    if action == "get":
        row = find(store, data.get("r") or data.get("token"))
        return {"ok": True, "row": row} if row else {"ok": False, "error": "not_found"}
    if action == "submit":
        token = uuid.uuid4().hex
        row = {
            "token": token,
            "submitted_at": now_hst(),
            "sign_number": data.get("sign_number") or "",
            "num_signs": data.get("num_signs") or "",
            "agent_name": data.get("agent_name") or "",
            "agent_phone": data.get("agent_phone") or "",
            "address": data.get("address") or "",
            "oh_date": data.get("oh_date") or "",
            "oh_end": data.get("oh_end") or "17:00",
            "returned": "N",
            "returned_at": "",
            "planned_return_date": "",
            "last_reminder_at": "",
            "reminder_count": 0,
            "fub_person_id": "",
            "notes": "",
        }
        if not row["sign_number"] or not row["agent_name"] or not row["agent_phone"] or not row["address"] or not row["oh_date"]:
            return {"ok": False, "error": "invalid"}
        nlist = numbers()
        if nlist:
            def d(s):
                return "".join(ch for ch in str(s) if ch.isdigit())
            if d(row["sign_number"]) not in [d(n) for n in nlist]:
                return {"ok": False, "error": "sign_number_not_on_list"}
        store["rows"].append(row)
        save_store(store)
        return {"ok": True, "token": token, "row": row}
    if action == "return":
        row = find(store, data.get("r") or data.get("token"))
        if not row:
            return {"ok": False, "error": "not_found"}
        row["returned"] = "Y"
        row["returned_at"] = now_hst()
        save_store(store)
        return {"ok": True, "row": row}
    if action == "plan":
        row = find(store, data.get("r") or data.get("token"))
        if not row:
            return {"ok": False, "error": "not_found"}
        row["planned_return_date"] = data.get("planned") or data.get("date") or ""
        save_store(store)
        return {"ok": True, "row": row}
    if action == "mark-sent":
        row = find(store, data.get("r") or data.get("token"))
        if not row:
            return {"ok": False, "error": "not_found"}
        row["last_reminder_at"] = data.get("sent_at") or now_hst()
        row["reminder_count"] = int(row.get("reminder_count") or 0) + 1
        if data.get("fub_person_id"):
            row["fub_person_id"] = data["fub_person_id"]
        save_store(store)
        return {"ok": True, "row": row}
    return {"ok": False, "error": "unknown_action"}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(SITE), **k)

    def log_message(self, fmt, *args):
        print("[%s] " % self.log_date_time_string() + fmt % args)

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode() if n else ""
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):
        if self.path.startswith("/mock-exec"):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            return
        self.send_error(404)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/mock-exec", "/mock-exec/"):
            q = {k: v[-1] for k, v in parse_qs(parsed.query).items()}
            self._json(handle(q.get("action"), q))
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/mock-exec", "/mock-exec/"):
            q = {k: v[-1] for k, v in parse_qs(parsed.query).items()}
            data = self._read_json()
            data.update({k: v for k, v in q.items() if k not in data})
            self._json(handle(data.get("action") or q.get("action"), data))
            return
        self.send_error(404)


def main():
    port = int(__import__("os").environ.get("PORT", "8765"))
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Talk Realty Open House Sign Out Sheet preview: http://127.0.0.1:{port}/open-house-sign-out-sheet/")
    print("Local mock API: /mock-exec  (does not write the live Google Sheet)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
