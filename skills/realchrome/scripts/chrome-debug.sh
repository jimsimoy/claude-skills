#!/bin/bash
# Start, inspect or stop a real Google Chrome instance with a dedicated profile and
# DevTools remote debugging bound to 127.0.0.1, for Claude to attach to over CDP.
#
#   chrome-debug.sh start [url]   launch (or reuse) the instance, optionally opening url
#   chrome-debug.sh status        print the Chrome version behind the debug port
#   chrome-debug.sh tabs          list open tabs (title + url)
#   chrome-debug.sh stop          quit ONLY the instance using this profile folder
#
# REALCHROME_PROFILE (default ~/.realchrome-profile) and REALCHROME_PORT (default 9222).
set -eu

PROFILE="${REALCHROME_PROFILE:-$HOME/.realchrome-profile}"
PORT="${REALCHROME_PORT:-9222}"
ENDPOINT="http://127.0.0.1:$PORT"
CHROME_APP="${REALCHROME_APP:-Google Chrome}"

is_up() { curl -s --max-time 2 "$ENDPOINT/json/version" >/dev/null 2>&1; }

case "${1:-}" in
  start)
    url="${2:-about:blank}"
    if is_up; then
      echo "already running on $ENDPOINT"
      if [ "$url" != "about:blank" ]; then
        curl -s --max-time 5 -X PUT "$ENDPOINT/json/new?$url" >/dev/null && echo "opened $url in a new tab"
      fi
      exit 0
    fi
    mkdir -p "$PROFILE"
    open -na "$CHROME_APP" --args \
      --user-data-dir="$PROFILE" \
      --remote-debugging-port="$PORT" \
      --remote-debugging-address=127.0.0.1 \
      --no-first-run --no-default-browser-check \
      "$url"
    for _ in $(seq 1 20); do
      if is_up; then echo "running on $ENDPOINT (profile $PROFILE)"; exit 0; fi
      sleep 0.5
    done
    echo "Chrome did not open the debug port on $PORT" >&2
    exit 1
    ;;
  status)
    if is_up; then
      curl -s "$ENDPOINT/json/version" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("Browser"))'
    else
      echo "not running on $ENDPOINT"
      exit 1
    fi
    ;;
  tabs)
    is_up || { echo "not running on $ENDPOINT" >&2; exit 1; }
    curl -s "$ENDPOINT/json/list" | python3 -c '
import json, sys
for t in json.load(sys.stdin):
    if t.get("type") == "page":
        print(t.get("title", "")[:60].ljust(60), t.get("url", ""))'
    ;;
  stop)
    if pgrep -f -- "--user-data-dir=$PROFILE" >/dev/null; then
      pkill -f -- "--user-data-dir=$PROFILE"
      echo "stopped the instance using $PROFILE"
    else
      echo "no instance using $PROFILE"
    fi
    ;;
  *)
    sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
