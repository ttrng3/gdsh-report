# Verification: the report pages

## Promise

The three pages https://ttrng3.github.io/gdsh-report/ serves (the generated dashboard, `/brief/`, `/review/`) are byte-identical to `main`. The dashboard shows the period the clock file and the history series were built for, carries its charts and no unfilled `{placeholder}`, and past months of the cumulative series never change. The run and the data are fresh. No private file, personal link, email address, account handle, Drive link or Drive id, and no word from another entity, is served; no personal trace sits in any tracked text file. The Cowork preview carries the dashboard `main` or the last run built.

## Clean state

```bash
cd ~/Projects/gdsh-report && git checkout main && git pull --ff-only
```
Run after a weekly check (the GDSH routine's cron, `0 1 * * 1` UTC = 08:00 Monday Hanoi, per pipeline-wiring's `collect_status.py` on 01/10), after a monthly publish, or after any merge. Wait for the merge's Pages run to go green first (`gh run list -w "Pages (allowlist)" -L1`).

## Steps

1. **Repo and live site** (on the Mac only; never from the GDSH routine, which must not fetch the live site: runbook "Verifying a run"). `python3 tools/verify_live.py --forbid <words>` → exit 0 and `"pass": true`. The words come from the runner's own notes (the other entity's name, any person's handle that leaked before). Names of people are never written into this repo. Without `--forbid` the entity verdict fails on purpose.
2. **Pages in Chrome.** Open each of https://ttrng3.github.io/gdsh-report/, `/brief/` and `/review/`. Run the script under Invariants on each. Expected: the page has a title and visible text; the dashboard draws as many `<svg>` charts as its file holds; nothing shows a raw `{placeholder}`.
3. **Console.** Reload each page, then read errors for `TypeError|ReferenceError|Uncaught|SyntaxError`. Expected: none (the pages carry no script; an error means something injected one).
4. **Preview.** Get the preview link from the GDSH routine's prompt (`RemoteTrigger get`). Never write it here. `Artifact list` its files and `Artifact read` its page into a file outside the repo (the session's scratch folder), under a neutral name. Build from `main` (`python3 tools/build-fragment.py`), then run `python3 tools/preview_matches.py <saved preview> build/artifact.html`. Expected: exit 0, `"match": true`. The script removes only the publisher's skeleton, pinned by its hash, and requires the rest to equal the build byte for byte. If it fails on `main`'s build, build from the last commit that changed `index.html` (`git log --first-parent -1 --format=%h -- index.html`, in a separate worktree) and run `main`'s script on it: `python3 tools/preview_matches.py <saved preview> <worktree>/build/artifact.html`. Use `main`'s script, because older commits do not have it. The fallback exists because the routine republishes only when `index.html` changed, so an unchanged dashboard leaves the preview as it was.

## Invariants

Step 1 prints these verdicts, all of which must be true: `served_equals_main`, `private_not_served`, `no_unfilled_placeholders`, `dashboard_has_charts` (exactly `EXPECTED_CHARTS`, 9 on 01/10), `period_consistent` (the clock's `asof` and period appear on the dashboard, and the history's newest month, the largest `T<n>`, is the clock's month), `history_months_kept` (every month in `history.json` as of the last two commits that changed it keeps its value, except the current month and the one before it, which each build writes: `build_auto.py`'s `_tN` and `_tPrev`), `heartbeat_fresh` (≤ 9 days, pipeline-wiring's watchdog for this pipeline), `data_fresh` (≤ 45 days, `freshness.py`'s `MAX_DATA_AGE_DAYS` default for this monthly source), `all_tracked_read`, `no_personal_traces`, `no_drive_refs_served`, `no_drive_ids_tracked` (runbook "The heartbeat": never a Drive id, 33 or 44 characters or the older `0B…` form, in this public repo), `no_preview_tags_tracked` (no Cowork preview version tag either), `no_forbidden_words`.

Step 2, in each page:
```js
const svgInFile=await fetch(location.pathname+'?v='+Date.now()).then(r=>r.text()).then(t=>(t.match(/<svg/g)||[]).length);
JSON.stringify({title:!!document.title.trim(), has_text:document.body.innerText.trim().length>500,
  charts_render:document.querySelectorAll('svg').length===svgInFile,
  no_raw_placeholder:!/\{[a-z_][a-z0-9_]*\}/.test(document.body.innerText)})
```
All of them must be true on all three pages.

## Adversary

- **A stranger on the public pages.** `private_not_served`: the README, CLAUDE.md, REVIEW.md, SETUP_AUTONOMY.md, the runbook, `history.json`, both clock files, the judgment layer, the review source, the build script, the tools, this protocol, one `work/` file found at run time, `freshness.py` and `.pages-allow` all exist on `main` and answer 404 live. `no_drive_refs_served`: no Drive link or id on a served page. `no_personal_traces` reads every tracked text file as well, because the repo is public. Matches are reported by count and file, never by value. Three known non-people are allowed by name in the script: GitHub's `noreply` commit address, the service-account placeholder in SETUP_AUTONOMY.md, and the generator's `@UPPER_CASE@` markers.
- **A build that half-ran.** `no_unfilled_placeholders` (a judgment-layer `{placeholder}` the build did not fill), `dashboard_has_charts`, `period_consistent`.
- **A run that rewrote a past month.** `history_months_kept`, against the last two commits that changed `history.json` (on 01/10 it had a single commit, so only that one exists to compare).
- **A routine that stopped running.** `heartbeat_fresh`. **A month that never got published:** `data_fresh`.
- **The other entity's data.** `no_forbidden_words` on the served pages.

## Sanctioned substitutes

- The forbidden word list is passed on the command line, so it can change without a PR. It proves the served pages don't contain those words; it cannot catch a name nobody has listed.
- The workbook cannot be fetched here, so the dashboard's figures are not re-derived: see Not covered.
- The preview cannot be fetched by a script, so step 4 is done by the runner with `Artifact list` and `Artifact read`.

## Evidence

- The JSON from step 1 and the three JSONs from step 2.
- Screenshots (`save_to_disk: true`): the top of each page.
- For step 4: the JSON `tools/preview_matches.py` printed.

## Not covered

- Whether the dashboard's figures equal the budget workbook: the workbook needs the Drive fetch (`fetch_latest_budget.py`), which needs secrets the repo does not have (`publish.yml` has never succeeded).
- Whether every figure in `/brief/` and `/review/` comes from a file in the source folder (the CLAUDE.md rule). They are hand-maintained; a reviewer checks the sources by eye.

## Traps

- Pages answers `cache-control: max-age=600` (10 minutes; response header seen with `curl -sI` on the sister dashboards, 01/10). A `served_equals_main` failure straight after a merge is the cache: wait for the Pages run, then re-run. Each request retries once on a network error or a 5xx.
- `index.html` is generated. A failing `period_consistent` or `no_unfilled_placeholders` is fixed in `gdsh_render.py`, `build_auto.py` or `judgment/judgment.html`, never in `index.html`.
- `data/index.json` is a clock, not a data store; the page does not read it. It can be older than the heartbeat by design: the weekly check writes only the heartbeat when no new month exists.
- The preview is published wrapped in a fixed skeleton (`<!doctype html>` … `<body>` and `</body></html>`), so its bytes never equal the build's. Step 4 compared whole-page hashes until 2026-10-02 and failed on a correct preview; `tools/preview_matches.py` removes exactly that skeleton (head pinned by sha256, tail exact). If the publisher changes its skeleton, step 4 fails until the pin is updated on purpose.
- `history.json` holds one series (`pnl_cum`) keyed `T<month>` with no year; `build_auto.py` writes keys in place and its month list runs `range(3, month+1)`, so the generator itself does not handle a new year (in January it would write `T0` and draw no months). Both history verdicts will go red at the first January publish, and stay red until the generator learns the year: that is the signal to fix `build_auto.py`, not the protocol (follow-up, 01/10).
- `HEARTBEAT_MAX` is 9 days (pipeline-wiring's watchdog for this weekly check); the runbook's 10 / 45 days are `freshness.py`'s run and data limits. `data_fresh` uses the 45.
- `git` errors stop the script's git-based verdicts as failures, never as "nothing to check".
