# Spec

Status: approved by Ty 02/10 (same conditions, "yes, go").

- New `tools/preview_matches.py <saved preview> [build]`: removes exactly the publisher's skeleton (the head through `<body>\n`, pinned by sha256 from the 02/10 preview; the tail `\n</body></html>`, exact) and requires the remaining bytes to equal the build byte for byte. Prints JSON; exit 0 only on a match. Nothing else is stripped or normalised.
- `verification/report-pages.md` step 4 runs it; Evidence and Traps say why.
- `tools/verify_live.py`: the new script is listed as private (must exist on main and 404 live).
- Promise: on the 02/10 preview, the script exits 0 against `main`'s build; it exits 1 when one byte of the build changes, when anything is added to the skeleton's head, when a second body tag appears, and when content follows the fragment.
