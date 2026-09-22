"""Report how long the published dashboard file has gone without changing."""
import datetime as dt
import os
import subprocess

path = os.environ.get("WATCH_PATH", "index.html")
max_age = int(os.environ.get("MAX_AGE_DAYS", "10"))

stamp = subprocess.run(
    ["git", "log", "-1", "--format=%cI", "--", path],
    capture_output=True, text=True, check=True).stdout.strip()

if not stamp:
    # No commit ever touched it — either the path is wrong or nothing has
    # ever been published. Both need a human, so flag it.
    print("last=never")
    print("days=-1")
    print("stale=true")
    raise SystemExit(0)

# git may hand back a trailing Z (commits made through the GitHub API do),
# which datetime.fromisoformat rejects before Python 3.11.
last = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
days = (dt.datetime.now(dt.timezone.utc) - last.astimezone(dt.timezone.utc)).days

print(f"last={last.date().isoformat()}")
print(f"days={days}")
print(f"stale={'true' if days > max_age else 'false'}")
