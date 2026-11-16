# Talk Realty Open House Sign Out Sheet — current setup

Live public page: https://talkrealty-open-house.onrender.com/open-house-sign-out-sheet/

TEST page (writes only to the **TEST** tab, never the live Sign-Outs log):

https://talkrealty-open-house.onrender.com/open-house-sign-out-sheet/?test=1

(also `.../open-house-sign-out-sheet/test/`, which redirects to `?test=1`)

Agents scan **one QR** and enter Name, Phone, and Open house location. The Apps Script backend assigns the next available sign color/number from `colors.json` (LockService so two submits cannot get the same color). The confirmation slowly fills the whole screen with that color (~1.8s; instant if the phone prefers reduced motion), then shows, in Playfair Display: "Your open house signs are the ones under the RED label." The color name is dynamic and uppercase in that line. The sign number sits smaller underneath, in a clean sans. A color stays out until Thursday Task Desk approval marks it returned, which frees it.

Live inventory is five sign sets (Red 808-378-7316; Blue, Green, Yellow, and Orange numbers pending). The page shows a live **Sign sets left: X of 5** counter (`?action=available`, plus `test=1` in TEST mode). TEST mode uses five sample colors with fake 555 numbers, shows a small TEST MODE badge, and has a **Reset test colors** link that frees every test color so you can cycle them and see the all-out message. FUB validation is a flag only (Verified agent column) and never blocks a submit. No FUB number routing.

Return reminder texts are cancelled. `reminders.py` is unused. There is no return page or return link on the public site. Do not schedule 6:30 PM or 12 PM text jobs.

## Thursday Task Desk

Routine command (posts one idempotent card; do not use until Christopher creates the routine):

```
python3 /workspace/jarvis/open-house-signout/thursday_card.py --post
```

Dry run (prints the card, posts nothing):

```
python3 /workspace/jarvis/open-house-signout/thursday_card.py
```

The card lists each currently-out color as one row (color, sign number, agent, sign-out date, location) with a Returned checkbox, plus one "Signs in office" count. Approving ticked colors writes Returned=Y to the Sheet and frees those colors. Number routing back to Christopher is later, after his list of numbers. No texts or emails.

## QR posters and wall labels

```
python3 /workspace/jarvis/open-house-signout/make_qr_sheet.py
python3 /workspace/jarvis/open-house-signout/make_qr_sheet.py --test
```

One poster QR for the single (live) sign-out page, plus a printable wall-label PDF (color dot + number) for each color. The `--test` command writes a TEST MODE poster at `/workspace/jarvis/open-house-signout/talkrealty-open-house-sign-out-TEST-qr.png` that opens the TEST URL. Sample live color: 808-378-7316 is red. Add the rest of the numbers in `colors.json` later (and on the live `site/open-house-sign-out-sheet/colors.json`).

## Apps Script — browser paste required (do this once)

Paste the updated `Code.gs` only after the static site is deployed. The live `/exec` URL should stay the same. In the Apps Script editor bound to the tracker Sheet `15m6e7Kk3hcrJ9dYGqeDqPektmAQxjlY0sRtiEvPAlks`:

1. Open https://script.google.com and open the project bound to that Sheet, named **Talk Realty Open House Sign Out Sheet**.
2. Open `Code.gs`. Select all and replace it with the entire contents of the local file `/workspace/jarvis/open-house-signout/Code.gs` (same text is also at `/workspace/jarvis/open-house-signout/apps-script/Code.gs`). Save (Ctrl/Cmd+S). Do not paste `.env` or any secrets into the file.
3. Optional, if not already set: Project Settings (gear) > Script properties > add `FUB_API_KEY` (same value as `.env`; never paste it in chat). This only fills the **Verified agent** column from a read-only FUB users check and never blocks a submit. If omitted, new rows get `not checked`. Leave `EXPORT_SECRET` as it already is.
4. Deploy > Manage deployments > the **existing** web app deployment > pencil / Edit > Version: **New version** (do not click "New deployment"). Execute as: Me. Who has access: Anyone. Deploy.
5. Confirm the `/exec` URL did not change. Open `/exec?action=health` and confirm it returns ok. A first health call will also add an empty **TEST** tab (headers only) next to Sign-Outs; existing tabs stay as they are.
6. Play on the TEST page first (`?test=1`), not the live form. Submit a few times to see colors cycle, then once more for the all-out message, then use **Reset test colors**. Rows land only on the TEST tab. After that is good, you can try one live sign-out and either delete that row or mark it returned on Thursday.

Until this redeploy happens, the live/test form will show the new page but submit cannot assign a color or write to the TEST tab (the deployed script still expects the old fields).

## Older notes

The sections below were written before go-live and still describe the first paste/deploy. Prefer the current section above.

# Talk Realty Open House Sign Out Sheet — setup (do not deploy yet)

Nothing in this folder has been deployed, shared, emailed, or enabled. The live tracker Sheet has no test rows.

Public name everywhere on the site, in `setTitle`, and in the Apps Script project / deployment name:

**Talk Realty Open House Sign Out Sheet**

Do not use "C Strickland" or "Christopher Strickland" on the site, in the header or footer, in HtmlService setTitle, or as the project name. Reminder texts may still say "Christopher at Talk Realty."

## What this is

Agents open a simple mobile website (a free Render static site that does not sleep). Submissions and returns are written by a Google Apps Script web app to the private tracker Sheet `15m6e7Kk3hcrJ9dYGqeDqPektmAQxjlY0sRtiEvPAlks`. A Lookup tab on that Sheet finds the agent name and cell from a sign number plus date.

Return links look like:

`https://YOUR-SERVICE.onrender.com/open-house-sign-out-sheet/return.html?r=TOKEN`

## Files

| Path | Role |
|---|---|
| `Code.gs`, `Index.html`, `Return.html` | Paste these three into the Apps Script editor (also copied under `apps-script/`) |
| `apps-script/appsscript.json` | Time zone Honolulu, web app access = anyone, no Google login |
| `site/` | Render static site publish folder (`/open-house-sign-out-sheet/`) |
| `site/open-house-sign-out-sheet/config.example.js` | Copy to `config.js` after you have the `/exec` URL. Never put `EXPORT_SECRET` here |
| `render.yaml` | Free Render static site Blueprint (not a Web Service) |
| `reminders.py` | Builds the noon / evening text list. Does not send |
| `.env.example` | Placeholder secrets for later |
| `local_preview.py` | Local site + mock API, does not touch the live Sheet |
| `monitor/check_uptime.py` | Headless check of the static path and `/exec?action=health` |
| `.github/workflows/uptime.yml` | GitHub Actions cron (schedule is commented out) |
| `tests/` | Fixture data and local tests |

## Browser session: paste and deploy the Apps Script (later, when asked)

1. Open the tracker Sheet: https://docs.google.com/spreadsheets/d/15m6e7Kk3hcrJ9dYGqeDqPektmAQxjlY0sRtiEvPAlks/edit
2. Extensions > Apps Script. If a stub file appears, delete its contents.
3. Name the project exactly: `Talk Realty Open House Sign Out Sheet`.
4. Paste `Code.gs` into `Code.gs`.
5. File > New > HTML and add `Index` and `Return`. Paste `Index.html` and `Return.html`.
6. (Optional) Project Settings > Show `appsscript.json`, replace with `apps-script/appsscript.json`.
7. Project Settings > Script properties: add `EXPORT_SECRET` with a long random value. Store the same value in `.env` and in GitHub Actions later. Do not put it in `config.js` or in chat.
8. Deploy > New deployment > type Web app.
   - Description: Talk Realty Open House Sign Out Sheet
   - Execute as: Me (cstrickland@pineapplehi.com)
   - Who has access: Anyone (agents should not need a Google login)
9. Authorize the spreadsheet scope when asked.
10. Copy the web app `/exec` URL. Put it in `site/open-house-sign-out-sheet/config.js` (from `config.example.js`) and in `.env` as `SIGN_OUT_EXPORT_URL` / `APPS_SCRIPT_EXEC_URL`.
11. Open `/exec?action=health` and confirm `{"ok":true,...}`. Submit one test sign-out on the preview or live site, confirm a row on the `Sign-Outs` tab, use the return link, then delete that test row. Do not leave fake data in the Sheet.

The first request also creates the `Sign-Outs` tab (headers only) and points the Lookup formulas at it.

## Render static site (later, when asked)

1. Create a Git repo from this folder (suggested name: `talk-realty-open-house-sign-out-sheet`). Do not commit `.env` or a filled `config.js`.
2. After the Apps Script URL exists, add `site/open-house-sign-out-sheet/config.js` from the example (or a deploy-time substitute) with `execUrl` and `publicBase`.
3. In Render, create a **Static Site** (or apply `render.yaml`). Publish path: `site`. This is not a free Web Service; free Web Services sleep, static sites do not.
4. Confirm:
   - `https://YOUR-SERVICE.onrender.com/open-house-sign-out-sheet/`
   - `https://YOUR-SERVICE.onrender.com/open-house-sign-out-sheet/return.html`
5. In the Render dashboard, add a Deploy Hook. Put that URL in GitHub Actions secret `RENDER_DEPLOY_HOOK_URL` only.

## Uptime monitor (later, when asked — do not enable yet)

Free headless option: GitHub Actions every 12 minutes, no AI.

`monitor/check_uptime.py` checks:

1. The static URL (HTTP 200 and the page title "Talk Realty Open House Sign Out Sheet")
2. `{APPS_SCRIPT_EXEC_URL}?action=health`

On failure it:

1. Emails cstrickland@pineapplehi.com.
2. If the **static** check failed, POSTs the Render deploy hook. If only Apps Script is down, it does not redeploy the static site (that would not fix it).
3. If `DOWN_WEBHOOK_URL` and `DOWN_WEBHOOK_KEY` are set, POSTs a small JSON payload to a Grok Bot routine webhook, with `Authorization: Bearer $DOWN_WEBHOOK_KEY`. The body includes which check failed, the HTTP status, and the time (Hawaii and UTC). It does not include secrets or hook URLs.

Those two webhook values are optional GitHub Actions secrets. Christopher pastes the URL and key himself; they are not in this repo and should never be printed or committed.

To turn it on later: uncomment the `schedule` cron in `.github/workflows/uptime.yml`, add the secrets listed in that file, and run one manual `workflow_dispatch` first.

Local dry run (no email, no hook, no webhook POST):

```bash
python3 monitor/check_uptime.py --static-url URL --exec-url URL
python3 monitor/check_uptime.py --static-url URL --exec-url URL --email --redeploy --webhook
# add --apply only when you really want to send the email, hook, and webhook
```

## How reminders.py reads the Sheet

Preferred free headless route: the Apps Script `/exec` export, not the browser and not a paid API.

```bash
# After deploy, with EXPORT_SECRET set in .env (never printed)
python3 reminders.py daily --url "$SIGN_OUT_EXPORT_URL"
```

That GETs `{SIGN_OUT_EXPORT_URL}?action=export&key={EXPORT_SECRET}` and receives JSON rows. The key must match the Script property. There is no public export without the key.

Local tests use a fixture instead of the live Sheet:

```bash
python3 reminders.py noon --input tests/sample/signouts.json --base-url https://example.onrender.com/open-house-sign-out-sheet --now "2026-11-15 12:05"
python3 reminders.py evening --input tests/sample/signouts.json --now "2026-11-15 18:30"
```

`daily` is an alias for `noon` (t4829u: a 12 PM HST check is enough). The evening job is still there if you want a same-day 6:30 PM text later.

After a text actually goes out in FUB, record it:

```bash
python3 reminders.py mark-sent --token TOKEN --sent-at "2026-11-16 12:05:00"
```

That updates `last reminder at` and `reminder count` on the Sheet (or in a local JSON file if you pass `--input`).

Reminders never send. FUB has no API text send. Each send is a FUB UI browser step, which costs more than a free API call. No texts after 9 PM HST (or before 8 AM HST). If a phone does not match exactly one FUB person, the item is flagged `needs_fub_contact` and no FUB record is created.

## Local preview (safe)

```bash
python3 local_preview.py
# http://127.0.0.1:8765/open-house-sign-out-sheet/
```

Uses `tests/sample/local-store.json` only.

## Costs and limits

- Render static site: free tier, does not sleep. Usage counts toward the workspace included outbound bandwidth and build (pipeline) minutes; overage can be billed. This site is a few small HTML files, so normal use should stay inside the included amount. Confirm current allowances at https://render.com/pricing.
- Apps Script web app: free, with Google daily quotas (URL fetches, script runtime). Fine for brokerage-scale sign-outs. The `/exec` URL is public for form posts; export and mark-sent stay locked behind `EXPORT_SECRET`.
- GitHub Actions: a 12-minute cron that runs a short Python check is typically a few dozen minutes per month, inside the included Actions minutes on a private repo and free on a public repo.
- Email alerts: Gmail (or other) SMTP. Free, needs an app password stored in Actions secrets.
- Down webhook: optional, no extra cost. Christopher pastes `DOWN_WEBHOOK_URL` and `DOWN_WEBHOOK_KEY` into Actions secrets himself.
- FUB people lookup: existing API key, read only.
- FUB texts: not an API. Browser sends have a real time / automation cost.
- No paid form host, no paid uptime SaaS, no AI in the monitor.

## Current brokerage form

The live Google Form was only read, never submitted. It is documented in `CURRENT-FORM.md`. It has no rider-number pick list. Put official numbers on the tracker’s Sign Numbers tab (column A, Active = Yes) when you have them; the site will then show a required dropdown. Until then, the sign number is a typed field.
