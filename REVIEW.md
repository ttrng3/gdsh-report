# REVIEW.md

What the reviewer agent (`agents/reviewer.md` in claude-config) checks on every PR to this repo. The three passes run in order, each in full. The last section holds this repo's own rules.

This file is never served: it is not in `.pages-allow`.

## Severity
- **Critical:** it will break something live or publish something it must not. A secret or token, personal data by value in a public repo, a newly served path that shouldn't be, a broken deploy, data loss, a gate bypass.
- **High:** wrong behaviour that will show up. A bug on a path that runs, a broken reference, a diff that does something other than what the PR says, a house rule broken in a way Ty would have to undo.
- **Medium:** it's wrong but contained. An edge case that isn't hit yet, a doc that disagrees with the code, a missing test for a changed behaviour.
- **Low:** clarity, naming, a stale comment.

When unsure between two levels, pick the higher one and say why.

## Pass 1: Bugs
- [ ] Logic: off-by-one, inverted condition, wrong variable, an unreachable branch, loop bounds.
- [ ] Edge cases: empty input, a missing file, a first run, a name with spaces or accents, a timezone (Hanoi is UTC+7; cron is UTC).
- [ ] References resolve: every path, heading anchor, script flag, workflow job name and file named in the diff exists in `files/` or in the base.
- [ ] Shell: quoting, `set -e` interactions, `$?` after a pipe, BSD vs GNU flags (the Mac runs BSD tools).
- [ ] Syntax: YAML, JSON, Python (3.9 on the Mac: no `match`, no `X | Y` types), HTML.
- [ ] The diff does what the PR description says, and nothing it doesn't say.

## Pass 2: Security
- [ ] Secrets by pattern: `ghp_`, `github_pat_`, `sk-`, `sk-ant-`, `AKIA`, `xox[bp]-`, private-key headers, `eyJ…` JWTs (a Supabase **service_role** JWT is always Critical), passwords in URLs, `?token=`/`?key=` in a link.
- [ ] Personal data **by value** in a public repo: a name with money, a phone number, an email address, an account number, an ID number. Referring to where the value lives is fine; the value itself isn't.
- [ ] Anything newly published: a path added to `.pages-allow`, or any new file in a repo still on legacy Pages.
- [ ] Workflow permissions widened (`permissions:`, `pull_request_target`, `secrets: inherit`), or a new third-party action not pinned to a sha.
- [ ] Test fixtures build fake secrets at run time; a token-shaped string typed into a file is a finding even if it's fake.

## Pass 3: House rules
- [ ] **Never by value:** a sensitive value is referenced, not quoted, in any file of a public repo, including `work/` docs.
- [ ] **Artifact mirror contract:** no Cowork preview URL and no artifact id in anything public or anything Ty is shown. (A registry row that records an id on the private Drive mount is the exception.)
- [ ] **Entity separation:** OMNI and ECOPM data, names and numbers never cross into each other's repo or page.
- [ ] **One change per `work/` folder:** the PR names its `work/<yymmdd>-<slug>/`; `intent.md` says accepted; `spec.md` says approved; the diff matches the spec's promise, with nothing extra.
- [ ] **`gate/` untouched** while it is frozen (until 2026-10-05).
- [ ] **One PR per merge command:** nothing in the diff merges or batches PRs (`gh pr merge` in a loop, the merge API).
- [ ] **Verify before you assert:** every number in a doc or page has a source named beside it or in its section.

## Repo-specific rules
Rules specific to gdsh-report. **Every standing ruling in the README and in `docs/gdsh-refresh.md` (the runbook, which outranks the routine prompt) applies as well; a PR that breaks one is at least High, and Critical where a line below says so.** The lines below are the ones most often at risk.

- **`index.html` is generated.** `gdsh_extract.py` → `gdsh_render.py` → `build_auto.py` produce it (runbook, "The chain"). A hand edit to `index.html` is High; the change belongs in the generator or in `judgment/judgment.html`.
- **`brief/` and `review/` are hand-maintained** and are not touched by the routine or `publish.yml` (README). A routine or workflow change that writes into them is High. `review/index.html` is built by `tools/build_review.py` from `review/src/B.html`.
- **The judgment layer is hand-edited and read-only to the build.** `build_auto.py` reads `judgment/judgment.html` and never writes it (runbook, "The judgment layer"). A build change that writes it is High.
- **Figures in judgment prose come through `{placeholders}`**, so the verdict can't disagree with the chart beside it. A new literal figure in the judgment prose that a placeholder could supply is High. An unknown placeholder or a missing block must keep stopping the build (runbook, "The judgment layer").
- **The generator reproduces the committed page byte for byte** (checked 2026-09-24, runbook "The judgment layer"). A generator change that alters output beyond the numbers must say so in the PR; unannounced, it is High.
- **Chart colours are tokens.** A new chart colour goes into `SVG_TOKENS` (or `CAT`) in `gdsh_render.py` (runbook, "Look"). A raw hex that bypasses them is High.
- **Light only, ruled 2026-09-24 by Ty.** No dark theme, no webfont (runbook, "Look").
- **Credentials.** `sa.json`, `budget.xlsx` and `fetch.out` are gitignored and deleted by the workflow's `if: always()` cleanup (runbook, "Credentials"). Committing any of them, or a token, is **Critical**. Only Ty sets the Actions secrets.
- **`data/index.json` is a clock, not a data store**; the page does not read it (runbook, "data/index.json"). Making the page depend on it is High.
- **The heartbeat stays.** `data/.last-check` is written on every workflow run, before anything else (runbook, "The heartbeat"). A diff that stops writing it is High.
- **Never fetch the live site from a routine** (runbook, "Verifying a run"). Such an instruction is High.
- **One address, one preview.** `https://ttrng3.github.io/gdsh-report/` is the only link. A Cowork preview URL or artifact id anywhere in the repo is **Critical** (the repo is public).
- **Don't widen what is published.** A new path in `.pages-allow`, or a new kind of data in `data/`, is High and needs Ty. (Carried from Omni-TMDV's REVIEW.md; not stated in this repo's own files.)
- **Entity separation.** The template rule in Pass 3 applies. This repo's files don't say which entity owns it, so until Ty rules, data from another project or entity is at least High and flagged for Ty.
