# Spec — Pages workflow: one glob dialect (approved)

Status: approved by Ty 30/09 via claude-config PR 12 (spec: claude-config
`work/260930-pages-glob-dialect/spec.md`, 39/39 Linux tests at 4817645).

## Change
`.github/workflows/pages.yml` becomes the template at 4817645 minus the optional placeholder comment, with gdsh-report's own workflow_run trigger kept in its place. Nothing else changes.

## Behaviour changes
- Only simple sets (`[abc]`, `[!x]`, `[^x]`) are allowed in `.pages-allow`; any other `[` or `]` stops the deploy.
- `[^x]` means "not x" in both checks.
- A backslash on any line, or any wildcard on an `@` line, stops the deploy.
- Header comment lists each fail-closed condition.

Pre-check 30/09 on this repo's main (comments stripped, grepped for a backslash or any `[`/`]`): 0 lines. So nothing changes on the site today.

## Pass condition (after merge)
First run `mode: live`, deploy green, served files byte-identical to the baseline in the PR body (path, HTTP status, first 12 hex of sha256); a file a routine changes in between is compared with its copy at the deployed commit. A failure reverts this PR.
