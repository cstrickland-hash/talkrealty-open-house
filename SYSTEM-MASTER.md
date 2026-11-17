# Open House Sign-Out System (master)

**Any change to this system must be added to this doc's change log the same day.**

This is the single source of truth for Talk Realty's open house sign-out website and everything that supports it. Future system updates must read this doc first and must not forget any rule, URL, deploy step, or pending item recorded here.

- Owner: Christopher Strickland, Talk Realty, Honolulu.
- Drive folder: [Jarvis Standards – Packets & Rules](https://drive.google.com/drive/folders/1jFGnY8dT-qma-wmF2tMF303JiWEaeCA8)
- Drive doc: https://docs.google.com/document/d/1E6zhj1qA1ycWklqzgotXEx8Vna_oru4HR24OPKNz9ZE/edit
- Box copy: `/workspace/jarvis/open-house-signout/SYSTEM-MASTER.md`
- Related rebuild guide (open house is section 7): [Jarvis Follow Up Automation: Prevention Rules and Rebuild Guide](https://docs.google.com/document/d/1l1IABR4rm_EGx2LfrfxHaODwJK-dg4B2Hp-x_DP9ZOw/edit) (box: `/workspace/jarvis/followup-failure/PREVENTION-RULES.md`)
- Rebuild / deploy notes: `/workspace/jarvis/open-house-signout/DEPLOY.md`

Never put secret values in this doc, in chat, in the static site, or in git. Name Script Properties and env var keys only.

## 1. Purpose and flow

Agents scan **one wall QR** and land on **one sign-out page**. They enter name, phone, and open house location. The Apps Script backend assigns the next free color and its phone number (LockService so two submits cannot get the same color). The confirmation screen fills slowly with that color, then tells the agent which color to take and what number is on those signs.

Agents **drop the signs off and leave**. There is **no agent return button** and **no reminder texts**. Christopher marks returns once a week on a private admin page, reached from a Thursday 9 AM HST Task Desk card.

Public name everywhere (site, `setTitle`, Apps Script project and deployment): **Talk Realty Open House Sign Out Sheet**. Do not use "C Strickland" or "Christopher Strickland" on the site, in the header or footer, or as the project name.

## 2. Live and test URLs, repo, and Render

- Live page: https://talkrealty-open-house.onrender.com/open-house-sign-out-sheet/
- TEST page (writes only to the **TEST Log** tab, never the live Sign-Out Log): https://talkrealty-open-house.onrender.com/open-house-sign-out-sheet/?test=1
  - Also `.../open-house-sign-out-sheet/test/`, which redirects to `?test=1`.
- Repo: https://github.com/cstrickland-hash/talkrealty-open-house (local box: `/workspace/jarvis/open-house-signout`, branch `main`)
- Render static site (free tier, does not sleep; not a Web Service):
  - Service id: `srv-dbt7q4ff3r2c73c6957g`
  - Workspace id: `tea-db1ar6bncjis73bva2tg`
  - Service name: `talkrealty-open-house`
  - Publish path: `site/`
  - Blueprint: `render.yaml` (`autoDeployTrigger: commit`). Root `/` redirects to `/open-house-sign-out-sheet/`.
- After a site change: commit and push the intended files, then trigger a Render deploy with **clearCache true** (Cloudflare can cache with s-maxage=300). Confirm the deploy is live, then verify with a cache-bust query and `last-modified` / `cf-cache-status`. Auto-deploy on commit exists, but typography and overlay deploys were API-triggered with clearCache so agents would not see a stale page.
- Do not commit: `.env`, screenshots, `Code.gs` / `apps-script/` (Apps Script is pasted in the browser; it stays off the public repo), `EXEC_URL.txt`, secret-bearing files, or unrelated dirty files. `config.js` is public (exec URL only, no secrets) and is committed.
- QR posters and wall labels: `python3 /workspace/jarvis/open-house-signout/make_qr_sheet.py` (add `--test` for the TEST poster). One poster QR for the live page, plus a printable wall-label PDF (color dot + number) for each color. Colored stickers go on top of each sign, and small colored strings wrap the handles so each set stays grouped and matches the wall labels.

## 3. Apps Script and Sheet

- Tracker Sheet: https://docs.google.com/spreadsheets/d/15m6e7Kk3hcrJ9dYGqeDqPektmAQxjlY0sRtiEvPAlks
  - Live tab: **Sign-Out Log** (legacy name **Sign-Outs** is still recognized).
  - Test tab: **TEST Log** (legacy name **TEST** is still recognized).
  - Visible columns (plain table, each with a pastel fill): Date/Time (HST), Agent Name, Agent Phone, Open House Location, Sign Color, Sign Number.
  - Hidden columns: token, Returned, Returned at.
  - Do not recreate Lookup or other helper tabs for new work.
- Apps Script project, bound to that Sheet: **Talk Realty Open House Sign Out Sheet**.
- Current deployment: **V9 is live**.
- Public `/exec` URL (already on the live site in `config.js`; not a secret):
  `https://script.google.com/macros/s/AKfycbyPQhA9ZI4aTu8rgxUvinenuGq1vyfhGh3sTU0k0jGJd87PvA_DVhuJ2We8zeC-0F6k/exec`
  - Also stored on the box at `/workspace/jarvis/open-house-signout/EXEC_URL.txt` (gitignored).
- **Always redeploy as a New version of the SAME deployment** so the `/exec` URL never changes. In the editor: Deploy > Manage deployments > the existing web app > pencil / Edit > Version: **New version** (do not click "New deployment"). Execute as: Me (`cstrickland@pineapplehi.com`). Who has access: Anyone (agents should not need a Google login).
- Box source to paste: `/workspace/jarvis/open-house-signout/Code.gs` (same text at `/workspace/jarvis/open-house-signout/apps-script/Code.gs`). Do not paste `.env` or any secrets into `Code.gs`.
- Backups on the box (not in the public repo): `Code.gs.v7.bak`, `apps-script/Code.gs.v7.bak`, `Code.gs.form-setup.bak`.
- Endpoints: `action=health`, `available` (plus `test=1`), `numbers`, `submit`, `return`, `office-count`, `test-reset`, `export`, `mark-sent`, plus the private admin page (`?admin=...`) and a secret-protected out-list (`?admin=...` with `&format=json` or `&action=out`). Export, mark-sent, office-count, and clear-logs need `EXPORT_SECRET`. The admin page and admin-out JSON accept `ADMIN_SECRET` or `EXPORT_SECRET` (V9).
- `LockService` stops two agents from getting the same color.
- After a Code.gs paste, open `/exec?action=health` and confirm it returns ok. Play on the TEST page first, never the live log, when verifying.

## 4. Secrets (names only, never values)

Script Properties in the Apps Script project (Project Settings > Script properties):

- `EXPORT_SECRET` — required for export / office-count / mark-sent / clear-logs, and accepted on the admin page (V9).
- `ADMIN_SECRET` — required for the private returns page at `?admin=...` and the admin-out JSON. V9 also accepts `EXPORT_SECRET` there.
- `FUB_API_KEY` — **pending**. Optional, read-only FUB users check for the Verified agent column (never blocks a submit; if omitted, new rows get `not checked`). Inbox switch-back after a return will use this property once it is added; it is not in Script Properties yet. Nothing is routed yet.

Where the same values live on the box (never commit, never print):

- `/workspace/jarvis/open-house-signout/.env`
- Template with key names only: `/workspace/jarvis/open-house-signout/.env.example`

Other key names that may appear in `.env` or GitHub Actions secrets for the uptime monitor (still never print values): `SIGN_OUT_EXPORT_URL` / `APPS_SCRIPT_EXEC_URL`, `SIGN_OUT_PUBLIC_BASE` / `STATIC_URL`, `RENDER_DEPLOY_HOOK_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `ALERT_EMAIL`, `DOWN_WEBHOOK_URL`, `DOWN_WEBHOOK_KEY`.

The admin secret may appear only in the Thursday card's private link field in the Task Desk state. Never print it, log it, put it in this doc, or put it in `config.js`.

## 5. Page rules

- Inventory is five sign sets, from `colors.json` on the box and on the live site (`site/open-house-sign-out-sheet/colors.json`). Pending colors still count toward the 5. Edit `colors.json` (keep the root copy in sync) to change numbers later.

  | Color | Number | Status |
  |---|---|---|
  | Red | 808-378-7316 (also 808-670-1135) | Primary is live. 670-1135 is an example second line, pending Devin confirm. |
  | Blue | 808-400-8551 | Example, pending Devin confirm. |
  | Green | 808-518-6893 | Example, pending Devin confirm. |
  | Yellow | 808-201-1994 | Example, pending Devin confirm. |
  | Orange | pending | Fifth 2026 line not confirmed yet. |

- The page shows a live **Sign sets left: X of 5** counter (`?action=available`, plus `test=1` in TEST mode). Sign phone numbers are **not** listed on the front page. After an agent signs out, the confirmation screen shows that color's number (from `colors.json` on the front end, so it is right even if the Apps Script backend still only knows Red). Example numbers get a small "example, pending Devin confirm" note. Test mode (`?test=1`) still uses the fake 555 numbers from the backend.
- Luxury listing feel: Playfair Display + Inter Tight, navy `#161b2e`, cream `#f7f4ee`, Compass and Hawaii luxury blend. Christopher's own background clip loops with a crossfade. The form card stays fixed. Fonts: Playfair Display 400;500;600 and Inter Tight.
- Color reveal: the screen fills slowly with the assigned color (~1.8s; instant if the phone prefers reduced motion), then shows in Playfair: "Your open house signs are the ones under the RED label." (color name is dynamic and uppercase). Underneath, a smaller Playfair line says **"Your open house signs phone number is"**, then the number on its own line, or **Pending** if that color has no number yet.
- Number typography (locked after mobile feedback, t4901u): the number is the second-biggest line, `clamp(1.9rem, 8vw, 2.6rem)`, Playfair 600, letter-spacing `0.08em`, margin-top `0.85rem`. The label stays smaller: `clamp(0.95rem, 2.6vw, 1.2rem)`, Playfair 400. Confirm copy max-width is `min(28rem, 92vw)` so the label does not wrap a lone "is".
- **No Reset test colors link on the color reveal screen**, including in `?test=1`, so agents never see it after they get a color (t4910u).
- When zero colors are left, **do not** use a separate full-screen all-out takeover. Keep the form visible but disabled behind a soft frosted overlay over the fill-in bar / form card (t4915u). Centered copy: **"All open house signs are currently out"** and, smaller, **"None are available right now. Please check back later."** Overlay style: absolutely positioned over `.form-stage`, cream `rgba(247,244,238,0.66)`, `backdrop-filter: blur(12px) saturate(1.05)`, Playfair title. Agents must not type, focus, or submit: disable the name, phone, location, and submit controls, set `aria-disabled`, `pointer-events: none`, and guard the submit handler. Name/phone autofill must remain harmless. **No reset link on this overlay.** The server still rejects a submit when none are left (`error: all_out`). After a successful fifth sign-out, the color reveal still shows; on a later page load with zero left, the overlay shows.
- Test mode (`?test=1`) writes only to the TEST Log and uses five sample colors with fake 555 numbers (Red starts at (808) 555-0101). A small TEST MODE badge is shown. A form-page "Reset test colors" link may still appear **below** the form card in test mode only; it is not on the reveal or the overlay. To free test colors, call `action=test-reset` with `test=1` by API or curl (**bot use only**). `resetTest_` uses the TEST Log only (`sheet_(true)`). **Never delete live log rows.** Leftover owner test rows (Red on Nov 15, Blue on Nov 16) were marked Returned (not deleted) on Nov 16 so the live counter can show all 5 in the office.
- localStorage autofill is per device: keys `talkrealty-oh-agent-name` and `talkrealty-oh-agent-phone`. Name and phone are restored on load (`restoreAgent`) and saved after a successful submit or an all-out response (`rememberAgent`). Autofill may populate fields even when the all-out overlay later locks the form; that is harmless.
- Instruction on the form: a compact bold-bordered alert, "Take only the signs from the color section you are given, and only signs that share that same phone number."
- FUB validation is a flag only (Verified agent column) and never blocks a submit.
- Return reminder texts are cancelled. `reminders.py` is unused. There is no return page or return link on the public site. Do not schedule 6:30 PM or 12 PM text jobs.

## 6. Returns

- Agents just drop signs off and leave. No agent return button, no reminder texts, no in-card checklist, no "signs in office" count.
- Christopher marks returns on the **private admin page** (`/exec?admin=...`), reached from the Thursday Task Desk card. One tap **Returned** per color: sets Returned=Y and Returned at (HST), frees that color, logs it, and calls the FUB inbox-routing hook (a no-op until `FUB_API_KEY` is in Script Properties). Append `&test=1` to manage TEST Log rows.
- **FUB inbox switch-back** (planned, not live): when a color is signed out, that number's FUB inbox will route to the agent; when Christopher taps Returned, it switches back to Christopher. Unanswered calls go to the inbox voicemail. This starts only after the numbers are confirmed and `FUB_API_KEY` is in Script Properties.
- Colors out more than 7 days are flagged as **carried over from last week** on the Thursday card and in the admin out-list (`days_out` / `days_out_label`).

## 7. Thursday 9 AM HST Task Desk card

Run this as part of the existing **"Task Desk watch + nightly failure digest"** routine, Thursday 9 AM HST:

```
python3 /workspace/jarvis/open-house-signout/thursday_card.py --post
```

- Dry run (prints a redacted card, posts nothing): `python3 /workspace/jarvis/open-house-signout/thursday_card.py --dry-run`
- TEST Log: add `--test`. Test desk post: `--test --post`.
- Posts one idempotent card when at least one color is still out. If none are out, the script skips posting. No texts or emails.
- The card lists each color still out (swatch, color, sign number, agent, location, days out). Colors out more than 7 days are marked carried over from last week. A private link on the card opens the admin returns page. ADMIN accepts `ADMIN_SECRET` or `EXPORT_SECRET` (V9).
- The script reads the secret-protected JSON at the same `/exec` URL plus `?admin=` and the secret, plus `&format=json` (or `&action=out`). Do not print the secret.

## 8. Site-down response

Free headless uptime check, no AI, no paid uptime SaaS.

- Script: `/workspace/jarvis/open-house-signout/monitor/check_uptime.py`
- Workflow: `.github/workflows/uptime.yml` (schedule every 12 minutes was enabled after a successful manual run, commit `bc79ab1`; also `workflow_dispatch`).
- Checks:
  1. The static URL (HTTP 200 and the page title "Talk Realty Open House Sign Out Sheet").
  2. `{APPS_SCRIPT_EXEC_URL}?action=health`.
- On failure it:
  1. Emails cstrickland@pineapplehi.com.
  2. If the **static** check failed, POSTs the Render deploy hook. If only Apps Script is down, it does not redeploy the static site (that would not fix it).
  3. If `DOWN_WEBHOOK_URL` and `DOWN_WEBHOOK_KEY` are set, POSTs a small JSON payload to a Grok Bot **site-down response routine**, with `Authorization: Bearer` and the key. The body includes which check failed, the HTTP status, and the time (Hawaii and UTC). It does not include secrets or hook URLs.
- Those two webhook values are optional GitHub Actions secrets. Christopher pastes the URL and key himself; they are not in the repo and must never be printed or committed.
- Local dry run (no email, no hook, no webhook POST):

```
python3 monitor/check_uptime.py --static-url URL --exec-url URL
python3 monitor/check_uptime.py --static-url URL --exec-url URL --email --redeploy --webhook
# add --apply only when you really want to send the email, hook, and webhook
```

The site-down response routine should alert Christopher and follow the path above: redeploy the static site only when the static check failed; do not clearCache-redeploy Render for an Apps Script-only outage.

## 9. Pending items

- Sign color numbers for Blue, Green, and Yellow are on the live page as **examples only**, marked "example, pending Devin confirm," from the 2026 lines proposed to Devin on Nov 15. They are not final until Devin or Christopher confirms them. Live Red remains 808-378-7316. 808-670-1135 is shown as a possible second Red line (example). Orange / the fifth line is still blank. Christopher emailed Devin to confirm on Nov 15, 2026, 8:55 PM HST.
- 2026 sign line candidates (from `/workspace/jarvis/open-house-signout/sign-lines-2026.md`, read only from FUB). These example numbers are now in `colors.json` and on the public sign list, clearly labeled as examples until confirmed. Do not print new physical sign riders from them until Christopher or Devin confirm:
  - Red: 808-378-7316 (the "talk oh signs (new 2026)" inbox, assigned only to Sophia Cretu). 808-670-1135 sits on the same inbox; it is unclear whether it is a second number or its own set.
  - 808-400-8551 ("talk Generic Open House Signs (new 2026)", no users assigned)
  - 808-518-6893 ("talk realty - Open House Sign")
  - 808-201-1994 ("201-1994 Open House Signs")
  - The fifth: 808-670-1135 or 808-353-5389 (unverified). Backup: 808-707-5644.
- Once Christopher sends how many signs go with each number, the reveal adds a **"Be sure you grab all X of X signs"** line (for example, "all 3 of 3").
- `FUB_API_KEY` is not in Script Properties yet. Verified-agent checks and FUB inbox switch-back wait on this. Do not route inboxes until the numbers are confirmed and the key is added (name only in docs; paste the value only in Script Properties and `.env`).
- The Thursday card command still needs to be confirmed as live inside the "Task Desk watch + nightly failure digest" routine prompt (parent applies routine prompt changes). Until then, the command and the 9 AM HST schedule are documented here so they are not forgotten.

## 10. Related files

- Site: `site/open-house-sign-out-sheet/` (`index.html`, `app.js`, `styles.css`, `config.js`, `colors.json`)
- Tests: `tests/test_site.py` (local site tests; no live Sheet writes)
- Local preview (safe, uses fixture data only; do not reuse another agent's leftover server on port 8765): `python3 local_preview.py`
- Current brokerage Google Form was only read, never submitted; notes in `CURRENT-FORM.md` (untracked). The live system is this website, not that form.

## 11. Change log

Add a dated line here the same day as any change to the site, Apps Script, inventory, returns flow, routines, or this doc.

### 2026-11-16 (Hawaii / Pacific/Honolulu)

- **~11:25 PM HST (t5118u).** Removed the Sign numbers list from the public front page (Christopher: the numbers belong on the confirmation screen after an agent gets a color). The confirm screen reads `colors.json` on the front end and shows the assigned number plus the "example, pending Devin confirm" note when it applies. Test mode still uses fake 555 numbers and the TEST Log only.
- **~11:20 PM HST (t5107u).** Added the 2026 example numbers to `colors.json` (Red 808-378-7316, also example 808-670-1135; Blue 808-400-8551; Green 808-518-6893; Yellow 808-201-1994; Orange still blank). The two leftover owner test sign-outs (Red Nov 15 "Remove this in 1 min Jarvis", Blue Nov 16 "123 bana") were marked Returned, not deleted, so the live counter can show 5 of 5 in the office. A short-lived front-page Sign numbers list was added, then removed the same night (see 11:25 PM).

### 2026-11-15 (Hawaii / Pacific/Honolulu)

- **~10:05 PM HST (t4919u).** Created this master Google Doc in Jarvis Standards – Packets & Rules, plus the box copy at `/workspace/jarvis/open-house-signout/SYSTEM-MASTER.md`. Rule: any change to this system must be added to this change log the same day. Linked from prevention rules section 7 and from `DEPLOY.md`.
- **~9:57 PM HST (t4915u), commit `762a512`, Render deploy `dep-dbtbes1srm7s73aq2320` (clearCache).** When no sign colors are left, the form stays visible but disabled behind a frosted overlay: "All open house signs are currently out" / "None are available right now. Please check back later." No reset link on the overlay. Test resets stay bot-only via the API. The old full-screen all-out takeover (and its test-mode reset link) were removed. Verified on the live TEST page by exhausting all 5 TEST colors (TEST Log only; live log left at 4 of 5 and never written), screenshotting desktop and 390px mobile to `/workspace/jarvis/open-house-signout/screenshots/all-out-overlay*.png` (not committed), then API test-reset back to TEST 5 of 5.
- **~9:41 PM HST (t4910u), commit `b081695`, Render deploy `dep-dbtb7cei0phs73f8220g`.** Removed the "Reset test colors" link from the color reveal screen entirely, including `?test=1`, so agents never see it after they get a color. The test-reset endpoint stays for bot/API use only. The form-page test-mode reset link below the card was left in place.
- **~9:32 PM HST (t4901u follow-up), commit `46e57c1`, Render deploy `dep-dbtb34bbc2fs73dl8pdg`.** Made the reveal phone number the second-biggest line: `clamp(1.9rem, 8vw, 2.6rem)`, Playfair 600, letter-spacing `0.08em`, margin-top `0.85rem`. Label stays `clamp(0.95rem, 2.6vw, 1.2rem)`.
- **~9:30 PM HST, commit `398fd2b`.** Widened the color reveal copy to `min(28rem, 92vw)` so the phone-number label stays on one line (no lone wrapped "is").
- **~9:24 PM HST (t4901u), commit `e59e6e1`.** Enlarged the color-reveal phone number and added the label "Your open house signs phone number is" above it, in Playfair. Uses each color's number or "Pending".
- **~8:55 PM HST.** Christopher emailed Devin to confirm the 2026 sign-line numbers. Answer due from Devin or at the Nov 16 meeting. Candidates documented in `sign-lines-2026.md` and in section 9 above; only Red 808-378-7316 is live.
- **~8:23 PM HST, commit `e980093`.** Fixed the sign-sets counter so it shows the live remaining count (not a stale or placeholder count).
- **~8:02 PM HST, commit `855c36e`.** Added the sign-out page background video from Christopher's clip (desktop and mobile encodes, poster image), looping with a crossfade. The form card stays fixed.
- **Apps Script V9 went live** (new version of the same `/exec` deployment; URL unchanged). Thursday 9 AM HST card via `thursday_card.py --post`, admin link on the card, ADMIN accepts `ADMIN_SECRET` or `EXPORT_SECRET`. Private admin page: one-tap Returned frees the color, logs it, and hooks FUB inbox switch-back (no-op until `FUB_API_KEY` is added). Carry-over flagging for colors out more than 7 days. Prior V8 paste/redeploy notes kept as history in `redeploy-v8.md`. V7 source backed up at `Code.gs.v7.bak`.
- **Return reminder texts cancelled.** `reminders.py` unused. No agent return button or public return page. Agents drop signs off; Christopher marks returns weekly from the Thursday card.
- **~7:12 PM HST, commit `8fc79e6`.** Calmed the sign-out page: no placeholder video, a static form card, a compact warning, and (then) a test counter of 3 of 5, later replaced by the live remaining count.
- **~7:07 PM HST, commit `220ad97`.** Refined typography to a Hawaii luxury and Compass blend (Playfair Display + Inter Tight).
- **~7:01 PM HST, commit `7003b1b`.** Added a live sign-sets counter and the luxury brokerage sign-out page. Live inventory set to five colors; Red 808-378-7316; other numbers pending.
- **~6:50 PM HST, commit `9c2afa0`.** Early reveal label "Your Phone Number" (later replaced by "Your open house signs phone number is").
- **~6:31 PM HST, commit `b089176`.** Added TEST mode (`?test=1`, TEST Log only, fake 555 numbers) and elegant color-reveal typography.
- **~6:24 PM HST, commit `226e1c5`.** Single sign-out page: assign the next free color, Thursday Task Desk card, one QR poster. `thursday_card.py` added.
- **~5:53 PM HST, commit `bc79ab1`.** Enabled the 12-minute uptime check schedule in GitHub Actions after a successful manual run.
- **~5:49 PM HST, commit `fa6fbd3`.** Set `publicBase` to the live Talk Realty Open House Sign Out Sheet URL.
- **~5:47 PM HST, commits `8004f63` and `f2b1556`.** Published the Talk Realty Open House Sign Out Sheet static site on Render and added the initial static site and Apps Script source.

