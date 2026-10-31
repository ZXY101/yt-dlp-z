#!/usr/bin/env bash
# Builds the frontend and starts the backend in test mode with throwaway state.
set -euo pipefail

E2E_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_DIR="$(dirname "$E2E_DIR")"
STATE_DIR="$E2E_DIR/.state/${PORT:-8765}"

rm -rf "$STATE_DIR"
mkdir -p "$STATE_DIR/downloads"

if [[ -z "${SKIP_FRONTEND_BUILD:-}" ]]; then
  npm run build --prefix "$REPO_DIR/frontend"
fi

export YTDLPZ_TEST_MODE=1
export YTDLPZ_FRONTEND_DIST="$REPO_DIR/frontend/dist"
export YTDLPZ_DEFAULT_DOWNLOAD_DIR="$STATE_DIR/downloads"
# The fake yt-dlp never touches the network (see stub/fake_yt_dlp.py).
# Channel feeds come from the test server itself (PUT /api/test/feeds/{channel_id}).
export YTDLPZ_YOUTUBE_FEED_URL="http://127.0.0.1:${PORT:-8765}/api/test/feeds/{channel_id}"
export YTDLPZ_YTDLP_COMMAND="[\"python3\", \"$E2E_DIR/stub/fake_yt_dlp.py\"]"
# The fake pip writes only package metadata, so yt-dlp updates never touch the network.
export YTDLPZ_YTDLP_PIP_COMMAND="[\"python3\", \"$E2E_DIR/stub/fake_pip.py\"]"
export YTDLPZ_PROXY_CHECK_COMMAND="[\"python3\", \"$E2E_DIR/stub/fake_proxy_check.py\"]"
exec uv run --project "$REPO_DIR/backend" yt-dlp-z \
  --port "${PORT:-8765}" --config-dir "$STATE_DIR/config"
