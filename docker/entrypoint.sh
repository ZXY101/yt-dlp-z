#!/bin/sh
# Runs the app as PUID:PGID so files in the mounted volumes get the host user's ownership.
set -eu

if [ "$(id -u)" != "0" ]; then
  exec "$@"
fi

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

groupmod --non-unique --gid "$PGID" app
usermod --non-unique --uid "$PUID" app

chown -R app:app /config
# Only the top level: the downloads folder may hold a large existing library.
chown app:app /downloads

exec gosu app "$@"
