#!/usr/bin/env python3
"""Derive the claude.ai artifact page from index.html.

The same markup cannot serve both surfaces. GitHub Pages needs a complete
document; the artifact service wraps whatever you publish in its own
<!doctype html><html><head>...</head><body>, so publishing a complete document
nests one inside another. The browser discards the inner <head>, every <style>
and <link> in it stops applying, and the page renders BLANK with no console
error — which gives you nothing to debug from.

Unlike Omni-TMDV, this renderer keeps its <title> inside <head>, so the
fragment cannot be cut at <title>. Instead the document wrappers are removed
and everything else is kept in source order.

Usage:
    python3 tools/build-fragment.py [out]      # default: build/artifact.html
"""
import pathlib
import re
import sys

# The \s and > alternatives matter: a bare `[^>]*` after `<head` also matches
# `<header>`, which silently deletes every header element on the page.
WRAPPERS = re.compile(
    r"<!doctype[^>]*>|</?(?:html|head|body)(?:\s[^>]*)?>", re.I)
BANNED = re.compile(
    r"<!doctype|<html[\s>]|</html>|<head[\s>]|</head>|<body[\s>]|</body>", re.I)


def build(src="index.html"):
    doc = pathlib.Path(src).read_text(encoding="utf-8")
    frag = WRAPPERS.sub("", doc)
    # The artifact service supplies its own charset and viewport meta, the
    # latter carrying viewport-fit=cover. A second viewport meta in the
    # fragment overrides it and loses the safe-area inset on a phone.
    frag = re.sub(r'\s*<meta[^>]*(charset|name=["\']?viewport)[^>]*>', "", frag, flags=re.I)
    frag = frag.strip() + "\n"

    if "<title>" not in frag.lower():
        sys.exit(f"{src}: no <title> survived — the artifact would be unnamed")

    leftover = BANNED.search(frag)
    if leftover:
        line = frag[:leftover.start()].count("\n") + 1
        sys.exit(f"{src}: document tag {leftover.group(0)!r} survives on line {line} "
                 "of the fragment — the artifact would render blank")

    # Collapse the run of blank lines the wrapper removal leaves behind.
    return re.sub(r"\n{3,}", "\n\n", frag)


def main(out="build/artifact.html"):
    frag = build()
    path = pathlib.Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frag, encoding="utf-8")
    print(f"{path}  {len(frag.encode()):,} bytes  (starts: {frag[:40]!r})")
    print("publish the data/ files FIRST, then this page on its own — a page sent in "
          "the same call as a large files payload has come back blank.")


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
