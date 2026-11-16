#!/usr/bin/env python3
"""Local tests for reminders.py. Uses fixture JSON, never the live Sheet."""
from __future__ import annotations

import json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SAMPLE = HERE / "sample" / "signouts.json"
SCRIPT = ROOT / "reminders.py"
BASE = "https://example.onrender.com/open-house-sign-out-sheet"
NOW = "2026-11-15 12:05"


def run(job, extra=None, now=NOW):
    cmd = [
        sys.executable, str(SCRIPT), job,
        "--input", str(SAMPLE),
        "--base-url", BASE,
        "--now", now,
        "--skip-fub",
    ]
    if extra:
        cmd.extend(extra)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(f"FAIL {job}: {p.returncode}\n{p.stdout}\n{p.stderr}")
    return json.loads(p.stdout)


def tokens(result):
    return [t["token"] for t in result["texts"]]


def main():
    evening = run("evening", now="2026-11-15 18:30")
    ev = tokens(evening)
    assert ev == ["tok_today"], ev
    assert "Christopher at Talk Realty" in evening["texts"][0]["message"]
    assert "return.html?r=tok_today" in evening["texts"][0]["message"]
    assert " - " not in evening["texts"][0]["message"].replace("https://", "")
    # URL hyphens are allowed; prose should not use spaced dashes
    prose = evening["texts"][0]["message"].split("https://")[0]
    assert "—" not in prose and "–" not in prose

    noon = run("noon", now="2026-11-15 12:05")
    nv = set(tokens(noon))
    assert "tok_yesterday" in nv, nv
    assert "tok_planned_passed" in nv, nv
    assert "tok_today" not in nv
    assert "tok_recent_reminder" not in nv
    assert "tok_planned_future" not in nv
    assert "tok_returned" not in nv

    daily = run("daily", now="2026-11-15 12:05")
    assert tokens(daily) == tokens(noon)

    late = run("noon", now="2026-11-15 21:00")
    assert late["texts"] == []
    assert late["skipped"] == "outside_send_window"

    # mark-sent against a temp copy
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "rows.json"
        path.write_text(SAMPLE.read_text())
        p = subprocess.run(
            [sys.executable, str(SCRIPT), "mark-sent", "--input", str(path),
             "--token", "tok_yesterday", "--sent-at", "2026-11-15 12:06"],
            capture_output=True, text=True,
        )
        assert p.returncode == 0, p.stderr
        out = json.loads(p.stdout)
        assert out["ok"] is True
        assert out["row"]["reminder_count"] == 1
        assert out["row"]["last_reminder_at"] == "2026-11-15 12:06"
        # After mark-sent, a noon run on the copy should skip this token (within 24h)
        p2 = subprocess.run(
            [sys.executable, str(SCRIPT), "noon", "--input", str(path),
             "--base-url", BASE, "--now", "2026-11-15 12:10", "--skip-fub"],
            capture_output=True, text=True,
        )
        res2 = json.loads(p2.stdout)
        assert "tok_yesterday" not in tokens(res2), res2

    print("reminders.py tests passed")
    print("sample evening text:")
    print(evening["texts"][0]["message"])
    print("sample noon text:")
    print(noon["texts"][0]["message"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
