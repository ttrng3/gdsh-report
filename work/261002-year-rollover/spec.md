# Spec: year-rollover

**Approved:** 2026-10-02 (Ty, in chat; December folded in at the same time)
**Post-review additions approved:** 2026-10-02 (Ty, in chat), as listed under Design "December", with two changes: December's card 6 shows "Đã hết năm ngân sách" once (its note), and its title stays bilingual like the other cards: "6 · Run-rate doanh thu: Thực hiện / Revenue run-rate: actual".

**Intent:** accepted 2026-10-02 · **Status:** approved

## Requirements
1. A build for a period in a new year starts a fresh series at T1 for that year, against that year's budget (intent, answer 1).
2. The 2026 months stay in `history.json` with every value unchanged. They are a record and are not drawn after 2026 (intent, answer 2).
3. The series starts in March for 2026 only. Every later year starts in January (intent, answer 3).
4. A build for the current period (08/2026) produces an `index.html` byte-identical to today's (intent, Outcome).
5. `verify_live.py`'s `period_consistent` and `history_months_kept` handle the new format and the new year, in the same PR. The Traps line about January leaves `verification/report-pages.md` (Ty's flag 2).
6. Nothing merges while the Monday 08:00 run is due (Ty's flag 3).
7. When no months remain (period 12), the run-rate card reads "Đã hết năm ngân sách" instead of a per-month need (Ty, 2026-10-02).

## Ty's three flags

**1. Does the key format change? Yes.** The keys go from `T<month>` to `YYYY-MM`, for example `T8` becomes `2026-08`. The year has to be in the key: otherwise `T1` of 2027 and the never-drawn months of later years collide with 2026's keys. A sorted key also gives the newest month directly.
- **Migration.** The PR rewrites `history.json` once: `T3…T8` become `2026-03…2026-08`, and every value stays the same. The check, to re-run after any rebase (it must print `True`):
  ```
  python3 -c "import json,subprocess;o=json.loads(subprocess.run(['git','show','origin/main:history.json'],capture_output=True,text=True,check=True).stdout)['pnl_cum'];n=json.load(open('history.json'))['pnl_cum'];print({f'2026-{int(k[1:]):02d}':v for k,v in o.items()}==n)"
  ```
- The PR carries a one-off check (run on the branch and printed in the PR body). It maps each old key `T<n>` to `2026-<nn>` and requires the two value sets to be equal key for key.
- **The build's seed values.** `build_auto.py`'s four seed values move to the new keys with the same numbers.
- **No ongoing legacy code in the build.** Only `verify_live.py` reads the old keys, and only from commits made before the migration.
- **Timing.** The migration is generated from `main`'s `history.json` at merge time. If Monday's run adds `T9` first, the branch is rebased and the check is re-run.

**2. The two checks change in the same PR.**
- `period_consistent`: the history's newest key (the largest `YYYY-MM`) must equal the clock's period (`MM/YYYY` → `YYYY-MM`).
- `history_months_kept`: older commits' `T<n>` keys are read as `2026-<nn>`. Every legacy key is a 2026 month, because the pipeline began in 2026. The months that may change are the current period and the month before it, but the month before only counts when it is in the same year.
- **Protocol text.** The Traps line about January is deleted. The two Invariants descriptions (`T<n>`, `_tN`/`_tPrev`) are reworded to the new keys.

**3. Do the routine or the runbook name the key format? No (Verified, 2026-10-02).**
- The GDSH routine's prompt (read live with `RemoteTrigger list`) only says to commit `history.json` exactly as `build_auto.py` writes it.
- `docs/gdsh-refresh.md`, `README.md`, `SETUP_AUTONOMY.md` and `publish.yml` name the file, never its keys.
- So the PR alone sets the format, and nothing in the routine changes.
- **Merge window.** The routine's next run is Mon 5 Oct, 01:00 UTC (08:00 Hanoi; `next_run_at` 01:13Z). Ship only after that run has finished and its commit, if any, has landed. Then rebase and re-run the migration check if `history.json` changed.

## Design
All in `build_auto.py`, unless noted:
- **Keys.** `_yy` = the period's year. History keys are `f"{_yy}-{_mm:02d}"`. The chart labels and the `{tN}` placeholder stay `T<month>`, which is what keeps today's page byte-identical.
- **Months drawn.** Start = 3 when `_yy == 2026`, otherwise 1. The months drawn are `range(start, _mm+1)` in the period's year only, and the chart points are labelled `T<n>` from the month number.
- **The month before.** It is written only when `_mm > 1`. In January the workbook's "lũy kế tháng trước" belongs to the new budget year, so nothing is written to the old year's December.
- **December.** Card 6 draws only the actual run-rate bar, and its note and tag read "Đã hết năm ngân sách"; no "T13" anywhere.
  - Added after review, 2026-10-02, recorded here so the spec matches the diff: in December the surge KPI also reads "Đã hết năm ngân sách", card 6's title becomes "6 · Run-rate doanh thu: Thực hiện / Revenue run-rate: actual", "Đã hết năm ngân sách" appears once on it (the note; no tag, the chart note gives only the unit), and its subtitle becomes "Doanh thu thực T12, tháng cuối của năm ngân sách.", and `{surge_x}` / `{surge_need_tr}` are not provided, so a December judgment that still quotes the surge stops the build as an unknown placeholder does. November's label reads "Cần T12".
  - Card 8's title and the P&L table header take the period's year instead of a literal 2026. With one point (January), card 5's subtitle no longer describes two lines.
  - `docs/gdsh-refresh.md` gains the December step: before the 12/YYYY build, rewrite or remove every judgment sentence that quotes the two surge placeholders. `{months}` is the months elapsed in the period's year (`_mm - start + 1`), and chart 5's plan line is allocated by month number, so a skipped month leaves no gap. Card 6's December bar shows the real figure; only the chart's scale has a floor.
- **`months` placeholder.** The months elapsed in the period's year. For 2026 this equals today's `_mm - 2`.
- **`gdsh_render.line2`.** A one-point series (January) would divide by zero (`step = plot_w/(n-1)`). With one point, the point is centred. Any series of two or more points draws exactly as today.
- **`tools/verify_live.py`.** The two verdicts as in flag 2.
- **`verification/report-pages.md`.** The Traps line goes, and the Invariants are reworded.
- **`history.json`.** Migrated once, same values.

## Conflicts
Loaded: kernel "standing-instructions.md", repo `CLAUDE.md`, the artifact-mirror contract (memory), the entity-separation rule, and secure-pages (below). Not loaded: the "ty-report-standard" and "apple-design" skills. The current page must not change by a byte, and January only changes how many points chart 5 draws, so there's no visual design decision.

| Rule (by name) | What in the design touches it | Resolution, or question for Ty |
|---|---|---|
| Repo CLAUDE.md: "`index.html` is generated … never hand-edit" | The page changes only through `build_auto.py` and `gdsh_render.py` | No conflict |
| Repo CLAUDE.md: writers of `history.json` are the routine and `publish.yml` | The PR edits `history.json` once, by hand, for the migration | Ty's ship of the PR authorises it; the check proves no value moved |
| Artifact-mirror contract | `index.html` is unchanged for 08/2026, so the preview needs no republish from this PR | No conflict |
| Ty's flag 3, merge window | The routine runs Mon 5 Oct 08:00 Hanoi | Ship after that run lands (above) |
| Year end, 12/2026 | The run-rate card would read "Cần T13–T12" | Resolved by Ty 2026-10-02: folded in (requirement 7) |
| Judgment layer for 01/2027 | `judgment/judgment.html` prose is written per period by the reviewer | Out of scope; the reviewer updates it as every month |

## Security (secure-pages, 2026-10-02)
```
1 Secrets ........ PASS (tree 0 hits, history 0, no JWT)
2 Visibility ..... PUBLIC — PASS for this change: it adds no data. history.json already holds OMNI P&L figures that the public dashboard shows; that is unchanged
3 Pages .......... PASS: Actions workflow, allowlist serves 4 HTML pages; history.json and data/ are "!" (not served)
4 Supabase ....... N/A (not used)
Verdict: safe to ship
```

## Promise
All of this runs on the branch, in temp copies, never on `main`'s data. The input is the real 08.2026 workbook from the Drive mount, read-only.
1. **Today, unchanged.** `GDSH_XLSX=<08.2026 workbook> GDSH_PERIOD=08/2026 GDSH_TODAY=20/09/2026 GDSH_OUT_DIR=<tmp, migrated history.json>`.
   - Pass: `cmp` with `main`'s `index.html` prints nothing.
   - The output `history.json` has the same values as `main`'s, key for key under the map.
   - Baseline already checked 2026-10-02: `main`'s own build reproduces `index.html` and `history.json` byte for byte.
2. **January 2027.** The same workbook with `GDSH_PERIOD=01/2027`, in a tmp copy.
   - Pass: the build exits 0.
   - Every `2026-*` value is unchanged, `2027-01` is added, and no `T0` or `2026-12` key is written.
   - Chart 5 draws exactly one actual point, labelled `T1`, and `{months}` = 1.
3. **December 2026.** `GDSH_PERIOD=12/2026` in a tmp copy. Pass: with today's judgment the build stops on the surge placeholder; with a judgment that does not quote it, the page shows "Đã hết năm ngân sách" and no "T13".
4. **February 2027.** Run on the January output. Pass: two points, `T1` and `T2`, and the 2026 values are still unchanged.
5. **The checks.** `verify_live.py` on the branch: `period_consistent` and `history_months_kept` are true, reading the pre-migration commits through the legacy map. In a throwaway worktree, a commit that changes one 2026 value makes `history_months_kept` false.
6. **After merge.** Reviewer before Ty's ship; the verifier on `main` after the ship and the Pages run.

The proof is measured on the branch before the PR is called ready; the verifier runs on the merge date.

## Out of scope
- Whether a 2027 workbook parses. `gdsh_extract.py` reads fixed 2026 columns ("NGÂN SÁCH T03-08", "Lũy kế 31/07"), and its guard stops the build on a layout it doesn't know. Assumption: the 2027 workbook will need its own extract change once it exists. This PR proves the generator's year logic using 2026 figures relabelled 01/2027.
- Judgment prose, `/brief/`, `/review/`, `/tom-tat/`.
