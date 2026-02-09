#!/bin/sh
set -e

export LISTEN_PORT="${PORT:-8080}"

envsubst '${LISTEN_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf

echo "nginx: listening on port ${LISTEN_PORT}"
