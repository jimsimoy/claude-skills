#!/usr/bin/env bash
#
# Local, offline transcription: local file or URL -> .txt + .vtt via whisper.cpp.
# Nothing leaves the machine — no cloud transcription API is used.
#
# Usage: ./transcribe.sh <audio-or-video-file-or-url> [output-dir]

set -euo pipefail

WHISPER_ROOT="${WHISPER_CPP_ROOT:-${HOME}/github.com/ggerganov/whisper.cpp}"
WHISPER_BIN="${WHISPER_ROOT}/build/bin/whisper-cli"
WHISPER_MODEL="${WHISPER_CPP_MODEL:-${WHISPER_ROOT}/models/ggml-medium.en.bin}"

require() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "Missing required tool: $1" >&2
        exit 1
    }
}

usage() {
    echo "Usage: $0 <audio-or-video-file-or-url> [output-dir]" >&2
    exit 1
}

[[ $# -ge 1 ]] || usage
SOURCE="$1"
OUT_DIR="${2:-.}"
mkdir -p "$OUT_DIR"

require ffmpeg
[[ -x "$WHISPER_BIN" ]] || {
    echo "whisper-cli not found at ${WHISPER_BIN}." >&2
    echo "Build whisper.cpp first: https://github.com/ggerganov/whisper.cpp#quick-start" >&2
    exit 1
}
[[ -f "$WHISPER_MODEL" ]] || {
    echo "Model not found at ${WHISPER_MODEL}." >&2
    echo "Download one with whisper.cpp's models/download-ggml-model.sh" >&2
    exit 1
}

fetch_url_as_mp3() {
    local url="$1"
    require yt-dlp
    local before after
    before=$(find "$OUT_DIR" -maxdepth 1 -name '*.mp3' 2>/dev/null | sort)
    yt-dlp \
        --extractor-args "youtube:player-client=android" \
        --no-playlist \
        --restrict-filenames \
        --extract-audio \
        --audio-format mp3 \
        --audio-quality 0 \
        -o "${OUT_DIR}/%(title).80s.%(ext)s" \
        -- "$url" >&2
    after=$(find "$OUT_DIR" -maxdepth 1 -name '*.mp3' 2>/dev/null | sort)
    comm -13 <(echo "$before") <(echo "$after") | head -1
}

to_mp3() {
    local raw="$1"
    local out="${OUT_DIR}/$(basename "${raw%.*}").mp3"
    if [[ -e "$out" ]]; then
        echo "$out"
        return
    fi
    ffmpeg -i "$raw" -codec:a libmp3lame -q:a 2 "$out" >&2
    echo "$out"
}

if [[ "$SOURCE" == http://* || "$SOURCE" == https://* ]]; then
    MP3=$(fetch_url_as_mp3 "$SOURCE")
    [[ -n "$MP3" && -e "$MP3" ]] || { echo "Download produced no audio file." >&2; exit 1; }
else
    [[ -e "$SOURCE" ]] || { echo "File not found: $SOURCE" >&2; exit 1; }
    MP3=$(to_mp3 "$SOURCE")
fi

BASE="${MP3%.mp3}"
echo "[transcribe] running whisper.cpp on: ${MP3}" >&2

"$WHISPER_BIN" \
    --output-txt \
    --output-vtt \
    --output-file "$BASE" \
    --model "$WHISPER_MODEL" \
    "$MP3" >&2

# Drop blank lines from the .vtt — pure noise for the downstream analysis pass.
sed -i.bak '/^$/d' "${BASE}.vtt" && rm -f "${BASE}.vtt.bak"

echo "${BASE}.vtt"
