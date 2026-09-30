# Spec — Pages workflow template v2 (approved)

Status: approved by Ty 30/09. Full spec: claude-config `work/260929-pages-template-fixes/spec.md`, with the defect fixes in `work/260930-pages-symlink-dir/` and `work/260930-pages-glob-spaces/`, pinned to claude-config 3f62fe2 (24/24 Linux tests in CI).

## Change
`.github/workflows/pages.yml` becomes the template at 3f62fe2 minus the optional placeholder comment. gdsh-report keeps its filled-in `workflow_run` trigger (GDSH monthly publish) in place of the placeholder comment. `.pages-allow` changes only its header comment, to describe the new rules.

## Behaviour changes (pre-checked on this repo 30/09: 0 uncovered files, 0 symlinks, no `./`, `//` or space in any line)
- Coverage reads every tracked file in a watched area, not the last diff; `fetch-depth: 50` is dropped.
- A `*` never matches a leading dot; a line containing `*`, `?` or `[` is a glob; a glob line is never split on spaces.
- Trimming uses parameter expansion (quotes taken literally).
- A symlink anywhere in a listed path, a path resolving outside the repo, or a path not written plainly stops the deploy; a tracked symlink in a watched area turns the run red.
- Permissions: workflow `contents: read`; build `contents: read` + `pages: read`; deploy `pages: write` + `id-token: write`. Proven live on Omni-TMDV 30/09.

## Pass condition (after merge)
The first run shows `mode: live` with configure-pages, upload and deploy green, and every served file byte-identical to the pre-merge baseline posted on the PR. A failure reverts this PR.
