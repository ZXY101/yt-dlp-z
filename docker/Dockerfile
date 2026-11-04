# syntax=docker/dockerfile:1

# The web app is plain static files, so build it natively even for other platforms.
FROM --platform=$BUILDPLATFORM node:26.13.0-slim AS frontend
WORKDIR /src
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/
COPY e2e/package.json e2e/
# --ignore-scripts skips the root lefthook install; the frontend needs no install scripts.
RUN npm ci --workspace frontend --ignore-scripts
COPY frontend/ frontend/
RUN npm run build --workspace frontend

FROM python:3.12-slim AS backend
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/src/ src/
RUN uv sync --frozen --no-dev --no-editable

# The font embedded in live chat overlays, so Japanese shows on players without CJK fonts. Only
# this one file is kept: the whole package is about 90 MB.
FROM python:3.12-slim AS chat-font
RUN apt-get update && apt-get install -y --no-install-recommends fonts-noto-cjk

FROM python:3.12-slim
# yt-dlp needs ffmpeg to merge and convert, and Deno to solve YouTube's JS challenges.
COPY --from=denoland/deno:bin-2.9.8 /deno /usr/local/bin/deno
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg gosu \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 app \
    && mkdir -p /config /downloads
COPY --from=backend /app/.venv /app/.venv
COPY --from=frontend /src/frontend/dist /app/frontend
COPY --from=chat-font /usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc /app/fonts/
COPY --from=chat-font /usr/share/doc/fonts-noto-cjk/copyright /app/fonts/NotoSansCJK-LICENSE
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH" \
    YTDLPZ_HOST=0.0.0.0 \
    YTDLPZ_PORT=9742 \
    YTDLPZ_CONFIG_DIR=/config \
    YTDLPZ_DEFAULT_DOWNLOAD_DIR=/downloads \
    YTDLPZ_FRONTEND_DIST=/app/frontend

EXPOSE 9742
VOLUME ["/config", "/downloads"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9742/api/health')"

ENTRYPOINT ["entrypoint.sh"]
CMD ["yt-dlp-z"]
