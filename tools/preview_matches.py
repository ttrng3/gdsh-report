#!/usr/bin/env python3
"""Step 4 of verification/report-pages.md: does a saved copy of the Cowork preview carry this build?

  python3 tools/preview_matches.py <saved-preview.html> [build/artifact.html]

The publisher wraps the fragment in a fixed skeleton: a head ending in "<body>\\n" and the tail
"\\n</body></html>". This removes exactly that skeleton and nothing else: the head must hash to
SKELETON_HEAD_SHA256 (pinned from the published preview on 2026-10-02) and the tail must be exact.
Then the fragment must equal the build byte for byte. If the publisher ever changes its skeleton,
this fails until the pin is updated on purpose. Prints JSON; exit 0 only on a match.
"""
import hashlib, json, pathlib, sys

SKELETON_HEAD_SHA256 = "65aeed0fe57327ab5aa05983225a4a29182a3b56007728748fc02df09a0df9b3"  # the 537-byte head, <!doctype html> through "<body>\\n"
ROOT = pathlib.Path(__file__).resolve().parent.parent
HEAD_END = b"<body>\n"
TAIL = b"\n</body></html>"


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    preview = pathlib.Path(sys.argv[1]).read_bytes()
    build = pathlib.Path(sys.argv[2] if len(sys.argv) == 3 else ROOT / "build/artifact.html").read_bytes()
    cut = preview.find(HEAD_END)
    head = preview[:cut + len(HEAD_END)] if cut >= 0 else b""
    out = {"skeleton_head_pinned": bool(head) and hashlib.sha256(head).hexdigest() == SKELETON_HEAD_SHA256,
           "skeleton_tail_exact": preview.endswith(TAIL)}
    # Head and tail must not overlap, and an empty build proves nothing.
    whole = out["skeleton_head_pinned"] and out["skeleton_tail_exact"] and len(preview) >= len(head) + len(TAIL)
    frag = preview[len(head):len(preview) - len(TAIL)] if whole and build else None
    if frag is not None:
        out.update(fragment_bytes=len(frag), build_bytes=len(build),
                   fragment_sha256=hashlib.sha256(frag).hexdigest(), build_sha256=hashlib.sha256(build).hexdigest())
    out["match"] = frag is not None and frag == build
    print(json.dumps(out, indent=1))
    sys.exit(0 if out["match"] else 1)


if __name__ == "__main__":
    main()
