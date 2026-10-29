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
exec uv run --project "$REPO_DIR/backend" yt-dlp-z \
  --port "${PORT:-8765}" --config-dir "$STATE_DIR/config"
