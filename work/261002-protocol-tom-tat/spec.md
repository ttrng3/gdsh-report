# Spec

Status: approved by Ty 02/10 ("approve", in chat).

- `tools/verify_live.py`: `tom-tat/index.html` joins `SERVED`, so the live page must equal main and is checked for unfilled placeholders, Drive references and forbidden words like the other three.
- `verification/report-pages.md`: the promise, step 2, Evidence and Not covered name `/tom-tat/`.
- Promise: step 1 exits 0 with `/tom-tat/` included; step 2 is all true on `/tom-tat/`; step 1 fails `served_equals_main` when one byte of `tom-tat/index.html` differs from what is served.
