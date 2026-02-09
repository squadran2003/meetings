#!/bin/sh
set -e

BACKEND_URL="${BACKEND_URL:-backend:8000}"
LISTEN_PORT="${PORT:-8080}"

envsubst '${BACKEND_URL} ${LISTEN_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf

echo "nginx: listening on port ${LISTEN_PORT}, proxying to ${BACKEND_URL}"
