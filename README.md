# GDSH Dashboard

Live dashboard: **https://ttrng3.github.io/gdsh-report/**

Board brief (BLĐ, 25/09/2026): **https://ttrng3.github.io/gdsh-report/brief/** — hand-written, lives in `brief/`, not touched by the routine or `publish.yml`.

BLĐ report (Bản B, 28/09/2026): **https://ttrng3.github.io/gdsh-report/review/** — built by `tools/build_review.py` from the doc export in `review/src/B.html`; hand-maintained like `brief/`.

**This repo is the source of truth.** A cloud routine writes `data/` and GitHub
Pages serves it. `docs/gdsh-refresh.md` is the runbook and outranks the routine
prompt and any stored memory.

    schedule → cloud routine → source → GitHub → Pages (the address) → artifact (Cowork preview)

**The Pages URL is the only link.** A Cowork preview exists and the routine
refreshes it last; its URL is never written anywhere (Ty's rule of 2026-09-26,
replacing 2026-09-23). See "One address, one preview" in `docs/gdsh-refresh.md`.
