# Intent: the GDSH dashboard keeps working when the period crosses into a new year

**Status:** accepted 2026-10-02
**Source:** pasted message in chat, 2026-10-02

**Problem.** `build_auto.py` assumes every period is in 2026 and the series starts in March:
- `history.json` keys its one series (`pnl_cum`) as `T<month>` with no year (`build_auto.py:71`, `:141–142`).
- The chart's month list is `range(3, month+1)` (`build_auto.py:143`), so in January it is empty and no months are drawn.
- The previous month is `T{month-1}` (`:71`), so a January build writes a `T0` key.
- Other values have the same assumption: `months=_mm-2` (`:170`, -1 in January) and the run-rate label "T{month+1}–T12" (`:151`).
- `verification/report-pages.md` Traps already says both history verdicts will go red at the first January publish (follow-up, 01/10).

Nothing is broken today. The first affected publish is the 01/2027 period.

**Outcome.** These can be checked on the branch, in a temp copy, never on `main`'s data:
- A simulated build for 01/2027 draws its months and keeps every 2026 value in `history.json` unchanged.
- A build for the current period produces a dashboard byte-identical to today's.
- `verify_live.py`'s `period_consistent` and `history_months_kept` handle the new year, and the January line leaves Traps.
- Then the reviewer, Ty's ship, and the verifier on `main`.

**Who and what is affected.**
- Repo gdsh-report: `build_auto.py`, `history.json`, `tools/verify_live.py`, `verification/report-pages.md`.
- The GDSH routine (Monday 08:00) and `publish.yml` (17th monthly), which both run the build.
- The live dashboard at /gdsh-report/. `/brief/`, `/review/` and `/tom-tat/` are hand-maintained and not touched.

**Constraints.**
- No 2026 value in `history.json` may change.
- Today's dashboard output must not change by a single byte.
- Entity: OMNI only.
- Nothing merges while the Monday 08:00 run is due.
- If the routine's prompt or runbook names the key format, the PR and the routine must agree.
- Never write the preview link or ids into the repo.

**Answers (Ty, chat, 2026-10-02).**
1. In 01/2027 the chart shows a fresh 2027 series from T1, against the 2027 budget.
2. The 2026 months stay in `history.json` as a record and are not drawn.
3. March was the start in 2026 only, because operations began then. Every later year starts in January.
