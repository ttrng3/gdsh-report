# GDSH Dashboard

Live dashboard: **https://ttrng3.github.io/gdsh-report/**

Board brief (BLĐ, 25/09/2026): **https://ttrng3.github.io/gdsh-report/brief/** — hand-written, lives in `brief/`, not touched by the routine or `publish.yml`.

Report versions (Bản A / Bản B, 28/09/2026): **https://ttrng3.github.io/gdsh-report/review/** — two tabs, built by `tools/build_review.py` from the tab exports in `review/src/`; hand-maintained like `brief/`.

**This repo is the source of truth.** A cloud routine writes `data/` and GitHub
Pages serves it. `docs/gdsh-refresh.md` is the runbook and outranks the routine
prompt and any stored memory.

    schedule → cloud routine → source → GitHub → Pages

**GitHub Pages is the only published surface** — there is no claude.ai artifact
copy, by Ty's ruling of 2026-09-23. See "One surface, on purpose" in `docs/gdsh-refresh.md`.
