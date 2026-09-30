# Spec (approved by Ty's ship of this PR)

- `.pages-allow` header: the sentence saying every run is a dry run until Pages is set to GitHub Actions is replaced; Pages has run from Actions since 2026-09-29 (`gh api repos/ttrng3/gdsh-report/pages` → build_type workflow, checked 30/09). The runbook says the public heartbeat names the source by period and file name, never a Drive id.
- Comment and doc text only: no published path, workflow or run step changes. Promise: the next Pages run is green and serves the same files.
