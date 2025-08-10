#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-jetson.local}"
PORT="${2:-8000}"

echo "Pinging ${HOST}..."
ping -c 3 "${HOST}" || true

echo "Health check:"
if ! curl -fsS "http://${HOST}:${PORT}/health"; then
  echo "Health endpoint not responding"
  exit 1
fi

