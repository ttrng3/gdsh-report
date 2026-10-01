#!/usr/bin/env python3
"""Machine half of verification/report-pages.md: is what Pages serves what main says, and is main sound?

Run from an up-to-date checkout of main:
  git pull --ff-only && python3 tools/verify_live.py --forbid WORD [WORD ...]

--forbid takes words that must not appear in a served page (another entity's name, a person's
account handle that leaked before). The runner supplies them so the list can change without a PR;
docs may name the other entity's label. Without them the entity check fails rather than passing unchecked.

Prints one JSON object of verdicts and exits 0 only when every verdict is true.
Matches of personal traces are reported by count and file, never by value.
"""
import argparse, datetime as dt, glob, hashlib, json, pathlib, re, subprocess, sys, time, unicodedata, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE = "https://ttrng3.github.io/gdsh-report/"
SERVED = ["index.html", "brief/index.html", "review/index.html"]  # .pages-allow
# Tracked but never served; each must exist on main and answer 404 live.
PRIVATE = ["README.md", "CLAUDE.md", "REVIEW.md", "SETUP_AUTONOMY.md", "docs/gdsh-refresh.md", "history.json",
           "data/index.json", "data/.last-check", "judgment/judgment.html", "review/src/B.html", "build_auto.py",
           "tools/build_review.py", "tools/verify_live.py", "verification/report-pages.md",
           ".github/scripts/freshness.py", ".pages-allow"]
# Storage links, full email addresses, and bare handles ("name@" with no domain).
TRACES = re.compile(r"/personal/|sharepoint\.com|1drv\.ms|[\w.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}|\b[a-z][a-z0-9._-]{2,}@(?![\w-])", re.I)
# Not people: GitHub's own commit address, the service-account placeholder in SETUP_AUTONOMY.md,
# and the generator's @UPPER_CASE@ template markers.
BENIGN = re.compile(r"users\.noreply\.github\.com|\.\.\.iam\.gserviceaccount\.com|^[A-Z_]+@$")
DRIVE = re.compile(r"(?:drive|docs)\.google\.com/|\b1[A-Za-z0-9_-]{32}\b")  # Drive links and file/folder ids
PLACEHOLDER = re.compile(r"\{[a-z_][a-z0-9_]*\}")  # a judgment-layer {placeholder} the build did not fill
HEARTBEAT_MAX = 9  # the watchdog pipeline-wiring's collect_status.py sets for this pipeline
DATA_MAX = 45      # MAX_DATA_AGE_DAYS default in .github/scripts/freshness.py (monthly source)


def get(path, tries=2):
    """One retry on a network error or a 5xx: a blip must not read as a mismatch."""
    url = f"{LIVE}{path}?v={int(time.time())}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "verify-live"}), timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return get(path, tries - 1) if e.code >= 500 and tries > 1 else (e.code, b"")
    except Exception as e:
        return get(path, tries - 1) if tries > 1 else (str(e), b"")


def age_days(stamp):
    """Days since an ISO stamp ('...Z', '+00:00', 3/6-digit fractions); None if unreadable."""
    try:
        t = dt.datetime.fromisoformat(stamp.strip().replace("Z", "+00:00"))
        t = t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
        return round((dt.datetime.now(dt.timezone.utc) - t).total_seconds() / 86400, 1)
    except (ValueError, AttributeError):
        return None


def norm(t):
    return unicodedata.normalize("NFC", str(t or "")).casefold()


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forbid", nargs="*", default=[])
    forbid = [norm(w) for w in ap.parse_args().forbid if w.strip()]
    v, info, live = {}, {}, {}

    for p in SERVED:
        st, body = get(p)
        live[p] = body
        info[p] = {"status": st, "live": hashlib.sha256(body).hexdigest()[:12],
                   "main": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:12] if (ROOT / p).exists() else None}
    v["served_equals_main"] = all(info[p]["status"] == 200 and info[p]["live"] == info[p]["main"] for p in SERVED)
    info["served_mismatch"] = [p for p in SERVED if info[p]["status"] != 200 or info[p]["live"] != info[p]["main"]]
    for p in SERVED:
        del info[p]

    work = sorted(glob.glob(str(ROOT / "work/*/intent.md")))[:1]  # any one work file, found at run time
    private = PRIVATE + [str(pathlib.Path(w).relative_to(ROOT)) for w in work]
    info["private_status"] = {p: get(p)[0] for p in private}
    info["private_missing_on_main"] = [p for p in private if not (ROOT / p).exists()] + ([] if work else ["work/*/intent.md"])
    v["private_not_served"] = all(s == 404 for s in info["private_status"].values()) and not info["private_missing_on_main"]

    pages = {p: (ROOT / p).read_text(encoding="utf-8") if (ROOT / p).exists() else "" for p in SERVED}
    info["unfilled"] = {p: len(set(PLACEHOLDER.findall(t))) for p, t in pages.items() if PLACEHOLDER.search(t)}
    v["no_unfilled_placeholders"] = not info["unfilled"]
    v["dashboard_has_charts"] = pages["index.html"].count("<svg") > 0

    # The dashboard's period must agree with the clock file and the history series it was built from.
    try:
        clock = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
        series = json.loads((ROOT / "history.json").read_text(encoding="utf-8")).get("pnl_cum", {})
        month = int(str(clock.get("period", "")).split("/")[0])
        last_key = list(series)[-1] if series else ""
        v["period_consistent"] = (clock.get("asof", "") in pages["index.html"] and
                                  f"{month:02d}.{str(clock['period']).split('/')[1]}" in pages["index.html"] and
                                  last_key == f"T{month}")
        info["period"] = {"clock": clock.get("period"), "history_last": last_key}
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError):
        clock, v["period_consistent"] = {}, False

    # Past months of the cumulative series never change: compare with the previous commit that touched it.
    # HEAD covers a working-tree edit; the commit before covers a run that already landed.
    prev = git("log", "-2", "--first-parent", "--format=%H", "--", "history.json").split()
    try:
        now = json.loads((ROOT / "history.json").read_text(encoding="utf-8")).get("pnl_cum", {})
        olds = [json.loads(git("show", f"{c}:history.json")).get("pnl_cum", {}) for c in prev]
        # A re-run of the current month may restate that month, so each old version's newest month is exempt.
        v["history_months_kept"] = all(now.get(k) == x for old in olds for k, x in list(old.items())[:-1])
        info["history_commits_compared"] = len(olds)
    except (OSError, ValueError, AttributeError):
        v["history_months_kept"] = False

    beat = ((ROOT / "data/.last-check").read_text(encoding="utf-8").split() or [""])[0] if (ROOT / "data/.last-check").exists() else ""
    info["heartbeat_age_days"], info["data_age_days"] = age_days(beat), age_days(str(clock.get("generatedUtc", "")))
    # -1 allows clock skew; a stamp further in the future (a wrong year) would otherwise pass forever.
    v["heartbeat_fresh"] = info["heartbeat_age_days"] is not None and -1 <= info["heartbeat_age_days"] <= HEARTBEAT_MAX
    v["data_fresh"] = info["data_age_days"] is not None and -1 <= info["data_age_days"] <= DATA_MAX

    # Served pages, live and on main, then every other tracked text file on main (the repo is public).
    texts = {f"live:{p}": b.decode("utf-8", "replace") for p, b in live.items()}
    texts.update({f"main:{p}": t for p, t in pages.items()})
    info["unreadable"] = []
    for p in [x for x in git("ls-files", "-z").split("\0") if x]:
        if p in SERVED or p in ("tools/verify_live.py", "verification/report-pages.md"):
            continue
        try:
            texts[f"main:{p}"] = (ROOT / p).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            pass  # binary file
        except OSError:
            info["unreadable"].append(p)
    v["all_tracked_read"] = not info["unreadable"]
    hits = {p: sum(1 for m in TRACES.finditer(t) if not BENIGN.search(m.group(0)) and not BENIGN.search(t[m.start():m.end() + 40]))
            for p, t in texts.items()}
    info["traces"] = {p: n for p, n in hits.items() if n}
    v["no_personal_traces"] = not info["traces"]
    served_texts = [t for k, t in texts.items() if k.split(":", 1)[1] in SERVED]
    info["drive_refs_served"] = sum(len(DRIVE.findall(t)) for t in served_texts)
    v["no_drive_refs_served"] = info["drive_refs_served"] == 0
    info["forbid_checked"] = len(forbid)
    v["no_forbidden_words"] = bool(forbid) and not any(w in norm(t) for w in forbid for t in served_texts)

    print(json.dumps({"pass": all(v.values()), "verdicts": v, "info": info}, ensure_ascii=False, indent=1))
    sys.exit(0 if all(v.values()) else 1)


if __name__ == "__main__":
    main()
