# Spec

Status: approved by Ty 01/10 (same words as the intent).

- `verification/report-pages.md`: promise, clean state, 4 steps (script, the three pages in Chrome, console, preview), invariants, adversary, sanctioned substitutes, evidence, not covered, traps.
- `tools/verify_live.py` (stdlib only, not served): 14 verdicts as JSON, exit 0 only when all pass: live equals `main` for the three served pages; private files exist and 404; no unfilled `{placeholder}`; the dashboard has exactly its 9 charts; the period agrees across the page, the clock file and the history; past months of the history unchanged against HEAD and the commit before; heartbeat (≤ 9 days) and data (≤ 45 days) fresh; every tracked text file read; no personal traces (by count and file; three named non-people allowed); no Drive link or id on a served page; no Drive id (33/44 characters or `0B…`) and no Cowork preview version tag in any tracked file; forbidden words (supplied at run time) absent from served pages.
- No change to any page, generator, data file, `.pages-allow` or runbook.
- Promise: once #9 (Drive ids and the preview tag out of the heartbeat) is merged, step 1 prints `"pass": true` against the live site and step 2 prints four trues on each of the three pages. Each drill breakage (unfilled placeholder, clock month the page lacks, a past month rewritten, a Drive link on a served page, an email in the README, an old heartbeat) fails its own verdict; an untouched copy and a restated newest month pass.
