# CLAUDE.md — gdsh-report

OMNI's GDSH budget dashboard, plus the hand-maintained board brief and BLĐ report, entity **OMNI**. Live: https://ttrng3.github.io/gdsh-report/ (also `/brief/` and `/review/`)

**If you are the scheduled routine:** follow the files your prompt names, `docs/gdsh-refresh.md` and `README.md`. They outrank this file. This file adds no step to a run.

## Commands
- Build the Cowork preview page: `python3 tools/build-fragment.py` (writes `build/artifact.html`). When the routine refreshes the preview is set by its runbook, not here. Never send `index.html` itself to the preview; Pages does serve it.
- Rebuild the BLĐ report after `review/src/B.html` changes: `python3 tools/build_review.py` (writes `review/index.html`)
- Freshness check, as the daily Action runs it: `python3 .github/scripts/freshness.py`

## Layout
- `index.html` is **generated**: `gdsh_extract.py` → `gdsh_render.py` → `build_auto.py`. Never hand-edit it; the change belongs in the generator or in `judgment/judgment.html`.
- `judgment/judgment.html` is the hand-edited judgment layer (verdict, #8 scenarios, Stage-Gate, questions, `review_asof`). The build reads it and never writes it; figures in its prose come through `{placeholders}`.
- `brief/` and `review/` are hand-maintained; neither the routine nor `publish.yml` touches them.
- Writers of `index.html`, `history.json`, `data/index.json` and `data/.last-check`: the routine and `publish.yml` (17th monthly). `data/index.json` is a clock the watchdog reads, not a data store; the page does not read it.
- `.pages-allow` lists what Pages publishes: `index.html`, `brief/index.html`, `review/index.html`. Every tracked file under a watched area needs a `.pages-allow` line (published, or `!` for known but not published); a new kind of file needs Ty's say-so and that line in its own PR first.
- `README.md` and `SETUP_AUTONOMY.md` explain the pipeline; `REVIEW.md` holds the reviewer's rules.

## Rules
- Changes reach `main` through a PR and Ty's ship. The only direct writes are the ones a routine's prompt and runbook allow, plus `publish.yml`'s own commits.
- The runbook and README win over this file and any memory note.
- Light only (Ty, 2026-09-24): no dark theme, no webfont. A new chart colour goes into `SVG_TOKENS` (or `CAT`) in `gdsh_render.py`.
- Never commit `sa.json`, `budget.xlsx`, `fetch.out` or a token. Only Ty sets the Actions secrets.
- Never write a Cowork preview URL or artifact id, a person's details or a secret into this public repo.
- Entity separation: this is OMNI. Never bring another company's data, names or numbers into this repo.
- In `brief/` and `review/`, every figure must come from a file in the source folder, or be a labelled estimate (2026-09-25).

## Known mistakes
- `publish.yml` has never succeeded: the repo has no secrets, so it stops at Preflight. A red run is that, not a regression; only Ty can add the secrets (2026-09-22).
- An old routine prompt said cloud sessions cannot push. True for shell `git push`, false for the GitHub MCP file tools (2026-09-22).
- Fetching https://ttrng3.github.io/ from a routine hits `CONNECT 403` and parks the run on a permission prompt (2026-09-22).
- A ToolSearch miss was read as a missing Artifact tool, and a routine skipped its mirror; attached tools never show in ToolSearch (2026-09-27).
- "No artifact link" means the preview URL stays out of sight, never that the preview goes; the 2026-09-23 "no artifact copy" text is withdrawn (2026-09-26).
- Brief files named `…Brief_HDQT-Tom-luoc_v2…v8` in Drive `Claude outputs/` came from other sessions and are not the current brief (2026-09-25).
