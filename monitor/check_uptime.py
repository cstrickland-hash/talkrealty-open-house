#!/usr/bin/env python3
"""Headless uptime check for Talk Realty Open House Sign Out Sheet.

Checks:
  1) the Render static path /open-house-sign-out-sheet
  2) the Apps Script /exec health endpoint

Does not use AI. On failure, exit 1 and print a short JSON report (no secrets).
Optional --redeploy, --email, and --webhook are dry-run unless --apply is set.

  python3 monitor/check_uptime.py --static-url URL --exec-url URL
  python3 monitor/check_uptime.py --static-url URL --exec-url URL --apply --email --redeploy --webhook
"""
from __future__ import annotations

import argparse, json, os, smtplib, ssl, sys, urllib.error, urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urljoin, urlparse

TITLE = "Talk Realty Open House Sign Out Sheet"


def load_env():
    env_path = Path(__file__).resolve().parent.parent / ".env"
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


def probe(url: str, expect_title: bool = False, timeout: int = 20) -> dict:
    result = {"url_host": urlparse(url).netloc, "ok": False, "status": None, "error": None, "has_title": False}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TalkRealtySignOutUptime/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(200000)
            result["status"] = resp.getcode()
            result["ok"] = 200 <= resp.getcode() < 300
            if expect_title:
                text = body.decode("utf-8", "replace")
                result["has_title"] = TITLE in text
                if result["ok"] and not result["has_title"]:
                    result["ok"] = False
                    result["error"] = "missing_title"
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = "http_error"
    except Exception as e:
        result["error"] = type(e).__name__
    return result


def health_url(exec_url: str) -> str:
    sep = "&" if "?" in exec_url else "?"
    return f"{exec_url}{sep}action=health"


def maybe_json(url: str) -> dict:
    result = probe(url, expect_title=False)
    if result["ok"]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TalkRealtySignOutUptime/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode())
            result["ok"] = bool(data.get("ok"))
            if not result["ok"]:
                result["error"] = "health_not_ok"
        except Exception:
            result["ok"] = False
            result["error"] = "health_parse"
    return result


def send_email(subject: str, body: str, apply: bool) -> str:
    to = os.environ.get("ALERT_EMAIL", "cstrickland@pineapplehi.com")
    host = os.environ.get("SMTP_HOST", "")
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    port = int(os.environ.get("SMTP_PORT", "587"))
    from_addr = os.environ.get("SMTP_FROM", user or "alerts@localhost")
    if not apply:
        return f"dry_run: would email {to} subject={subject!r}"
    if not host or not password:
        return "skipped: SMTP secrets not set"
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.set_content(body)
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        if user:
            smtp.login(user, password)
        smtp.send_message(msg)
    return f"sent to {to}"


def redeploy(apply: bool) -> str:
    hook = os.environ.get("RENDER_DEPLOY_HOOK_URL", "")
    if not apply:
        return "dry_run: would POST the Render deploy hook"
    if not hook:
        return "skipped: RENDER_DEPLOY_HOOK_URL not set"
    req = urllib.request.Request(hook, method="POST", data=b"", headers={"User-Agent": "TalkRealtySignOutUptime/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        code = resp.getcode()
    return f"deploy hook HTTP {code}"


def failed_checks(static: dict, apps_res: dict) -> list[dict]:
    failed = []
    if not static.get("ok"):
        failed.append({
            "check": "static",
            "status": static.get("status"),
            "error": static.get("error"),
        })
    if not apps_res.get("ok"):
        failed.append({
            "check": "apps_script",
            "status": apps_res.get("status"),
            "error": apps_res.get("error"),
        })
    return failed


def webhook_payload(static: dict, apps_res: dict, checked_at_utc: str) -> dict:
    now_hst = datetime.now(ZoneInfo("Pacific/Honolulu")).strftime("%Y-%m-%d %H:%M:%S HST")
    return {
        "service": TITLE,
        "event": "down",
        "time": now_hst,
        "time_utc": checked_at_utc,
        "failed": failed_checks(static, apps_res),
    }


def notify_webhook(payload: dict, apply: bool) -> str:
    """POST a small down payload to a Grok Bot routine webhook. Optional.

    Christopher pastes DOWN_WEBHOOK_URL and DOWN_WEBHOOK_KEY himself.
    The key is sent as Authorization: Bearer. Never printed.
    """
    url = os.environ.get("DOWN_WEBHOOK_URL", "")
    key = os.environ.get("DOWN_WEBHOOK_KEY", "")
    if not apply:
        failed = ",".join(item["check"] for item in payload.get("failed") or []) or "none"
        return f"dry_run: would POST down webhook (failed={failed})"
    if not url:
        return "skipped: DOWN_WEBHOOK_URL not set"
    if not key:
        return "skipped: DOWN_WEBHOOK_KEY not set"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "User-Agent": "TalkRealtySignOutUptime/1.0",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return f"down webhook HTTP {resp.getcode()}"


def main(argv=None) -> int:
    load_env()
    p = argparse.ArgumentParser()
    p.add_argument("--static-url", dest="static_url", default=os.environ.get("STATIC_URL", ""))
    p.add_argument("--exec-url", dest="exec_url", default=os.environ.get("APPS_SCRIPT_EXEC_URL", ""))
    p.add_argument("--apply", action="store_true", help="Actually email / redeploy / POST the down webhook")
    p.add_argument("--email", action="store_true")
    p.add_argument("--redeploy", action="store_true")
    p.add_argument("--webhook", action="store_true")
    args = p.parse_args(argv)

    if not args.static_url or not args.exec_url:
        print("Need --static-url and --exec-url (or STATIC_URL and APPS_SCRIPT_EXEC_URL)", file=sys.stderr)
        return 2

    static_url = args.static_url
    if not static_url.rstrip("/").endswith("open-house-sign-out-sheet"):
        static_url = urljoin(static_url.rstrip("/") + "/", "open-house-sign-out-sheet/")
    if not static_url.endswith("/"):
        static_url += "/"

    static = probe(static_url, expect_title=True)
    script = health_url(args.exec_url)
    apps_res = maybe_json(script)

    report = {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "static": static,
        "apps_script": apps_res,
        "ok": bool(static.get("ok") and apps_res.get("ok")),
        "actions": [],
    }

    if not report["ok"]:
        parts = []
        if not static.get("ok"):
            parts.append("static site")
        if not apps_res.get("ok"):
            parts.append("Apps Script")
        subject = "Talk Realty Open House Sign Out Sheet is down (" + " and ".join(parts) + ")"
        body = (
            "The uptime check failed.\n\n"
            + json.dumps(report, indent=2)
            + "\n\nThis email does not include secrets or deploy hook URLs.\n"
        )
        if args.email or args.apply:
            report["actions"].append(send_email(subject, body, args.apply))
        if args.webhook or args.apply:
            payload = webhook_payload(static, apps_res, report["checked_at"])
            try:
                report["actions"].append(notify_webhook(payload, args.apply))
            except Exception as e:
                report["actions"].append("down webhook error: " + type(e).__name__)
        # Redeploy the static site only when that check failed. Redeploying will not fix Apps Script.
        if (args.redeploy or args.apply) and not static.get("ok"):
            try:
                report["actions"].append(redeploy(args.apply))
            except Exception as e:
                report["actions"].append("deploy hook error: " + type(e).__name__)
        elif (args.redeploy or args.apply) and static.get("ok"):
            report["actions"].append("static site is up; skipped deploy hook")

    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
