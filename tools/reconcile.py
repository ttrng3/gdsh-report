#!/usr/bin/env python3
"""Compare two copies of a dashboard's data and say which one is authoritative.

GitHub Pages and the claude.ai artifact each hold their own copy of `data/`,
because an artifact cannot fetch across origins. Two copies can drift. This
says whether they have, and which way to sync.

It is deliberately shape-agnostic. These dashboards do not share a schema:

    OMNI         history[].week   + ISO `generated`      slices in data/weeks/
    ECOPM        wk[].id          + `generatedUtc`       slices in data/weeks/
    ECP x ELA    weeks{} manifest + `generatedUtc`       slices in data/weeks/
    TMDV         panels{} manifest+ `generatedUtc`       slices in data/panels/

Earlier versions hardcoded one shape at a time, and each new dashboard was
silently read as "zero slices" — which reports IN SYNC no matter what drifted.
So the manifest key and the slice directory are both discovered, not assumed,
and an index with no recognisable manifest is an error rather than an empty
comparison.

Usage:
    python3 tools/reconcile.py <dir-a> <dir-b>

Each directory is a `data/` tree. Exits 0 when they agree, 1 when they differ.
"""
import json
import pathlib
import sys

MANIFESTS = ("history", "wk", "weeks", "panels", "periods", "runs")


def slices(root):
    """Every *.json under data/, keyed by path relative to data/ (minus .json)."""
    root = pathlib.Path(root)
    out = {}
    for p in sorted(root.rglob("*.json")):
        if p.name == "index.json":
            continue
        out[str(p.relative_to(root).with_suffix(""))] = p.read_text(encoding="utf-8")
    return out


def load(root):
    idx = json.loads((pathlib.Path(root) / "index.json").read_text(encoding="utf-8"))
    return idx, slices(root)


def stamp(idx):
    return idx.get("generatedUtc") or idx.get("generated", "")


def entries(idx, where):
    """manifest key -> entry, whichever shape this index uses."""
    for key in MANIFESTS:
        v = idx.get(key)
        if isinstance(v, list):
            return {e.get("week") or e.get("id"): e for e in v}
        if isinstance(v, dict):
            return {k: {"slice": s} for k, s in v.items()}
    sys.exit(f"{where}/index.json has none of {MANIFESTS} — cannot compare; "
             "add the new shape to MANIFESTS rather than letting it pass.")


def main(a_dir, b_dir):
    (a_idx, a_sl), (b_idx, b_sl) = load(a_dir), load(b_dir)
    diffs = []

    a_gen, b_gen = stamp(a_idx), stamp(b_idx)
    if a_gen != b_gen:
        diffs.append(f"generated differs: {a_dir}={a_gen}  {b_dir}={b_gen}"
                     f"  -> newer: {a_dir if a_gen > b_gen else b_dir}")

    a_e, b_e = entries(a_idx, a_dir), entries(b_idx, b_dir)
    for k in sorted(set(a_e) ^ set(b_e)):
        diffs.append(f"entry only in {a_dir if k in a_e else b_dir}: {k}")
    for k in sorted(set(a_e) & set(b_e)):
        if a_e[k] != b_e[k]:
            fields = sorted(f for f in set(a_e[k]) | set(b_e[k])
                            if a_e[k].get(f) != b_e[k].get(f))
            diffs.append(f"entry {k} differs on: {', '.join(fields)}")

    for s in sorted(set(a_sl) ^ set(b_sl)):
        diffs.append(f"file only in {a_dir if s in a_sl else b_dir}: {s}.json")
    for s in sorted(set(a_sl) & set(b_sl)):
        if a_sl[s] != b_sl[s]:
            diffs.append(f"file {s}.json differs "
                         f"({len(a_sl[s]):,} vs {len(b_sl[s]):,} chars)")

    if not diffs:
        print(f"IN SYNC — {len(a_e)} entries, {len(a_sl)} files, generated {a_gen}")
        return 0
    print(f"DRIFT — {len(diffs)} difference(s):")
    for d in diffs:
        print("  -", d)
    print("\nThe copy with the newer generation stamp is authoritative. Copy "
          "its files over the other, then republish that side.")
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
