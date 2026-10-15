#!/usr/bin/env bash
# localsave — copy the current Claude Code session's transcript to local disk.
# Refuses, and writes nothing, in a Claude Code web (cloud) session.
#
# Usage:  localsave.sh "<short topic>"     save; prints the folder it saved into
#         localsave.sh --check             report whether saving is allowed; writes nothing
# Env:    LOCALSAVE_DIR      destination root (default: $HOME/claude-conversations)
#         CLAUDE_CONFIG_DIR  Claude Code config dir (default: $HOME/.claude)
# Exit:   0 saved / allowed, 3 refused
set -eo pipefail   # no -u: macOS bash 3.2 treats an empty array as unbound

DEST_ROOT="${LOCALSAVE_DIR:-$HOME/claude-conversations}"
CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

refuse() { echo "REFUSED: $1. Nothing was saved." >&2; exit 3; }

# 1. Local-session gate. Claude Code on the web sets CLAUDE_CODE_REMOTE=true.
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] && refuse "this is a Claude Code web (cloud) session"

# 2. Find this session's local transcript.
ID="${CLAUDE_CODE_SESSION_ID:-}"
[ -n "$ID" ] || refuse "CLAUDE_CODE_SESSION_ID is not set (not running inside Claude Code?)"
case "$ID" in *[!A-Za-z0-9-]*) refuse "unexpected session id format" ;; esac
shopt -s nullglob
matches=("$CONFIG_DIR"/projects/*/"$ID".jsonl)
[ "${#matches[@]}" -eq 1 ] || refuse "expected 1 local transcript for session $ID under $CONFIG_DIR/projects, found ${#matches[@]}"

# 3. Never save into a git work tree unless the destination is gitignored there,
#    so a later `git add .` can't commit or push a transcript.
SLUG="$(printf '%s' "${1:-session}" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//; s/-$//' | cut -c1-50)"
DIR="$DEST_ROOT/$(date +%F)_${SLUG:-session}_${ID:0:8}"
probe="$DEST_ROOT"; while [ ! -d "$probe" ]; do probe="$(dirname "$probe")"; done
if top="$(git -C "$probe" rev-parse --show-toplevel 2>/dev/null)"; then
  git -C "$top" check-ignore -q "$DIR/transcript.jsonl" \
    || refuse "$DEST_ROOT is inside git repo $top but not gitignored there (add it to .gitignore, or set LOCALSAVE_DIR elsewhere)"
fi

if [ "${1:-}" = "--check" ]; then
  echo "OK: local session, transcript found, destination $DEST_ROOT is safe"
  exit 0
fi

# 4. Save (re-running for the same session and day overwrites with a newer snapshot).
umask 077
mkdir -p "$DIR"
cp "${matches[0]}" "$DIR/transcript.jsonl"
chmod 600 "$DIR/transcript.jsonl"
echo "$DIR"
