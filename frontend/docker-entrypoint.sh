#!/bin/sh
set -e

export BACKEND_URL="${BACKEND_URL:-backend:8000}"
export LISTEN_PORT="${PORT:-8080}"

envsubst '${BACKEND_URL} ${LISTEN_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf

echo "nginx: listening on port ${LISTEN_PORT}, proxying to ${BACKEND_URL}"
