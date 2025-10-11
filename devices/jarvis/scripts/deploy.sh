#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/valthera/valthera}"
BASE_COMPOSE="${BASE_COMPOSE:-$REPO_DIR/devices/jarvis/docker-compose.yml}"
OVERRIDE_YML="${OVERRIDE_YML:-$REPO_DIR/devices/jarvis/jetson.jarvis.override.yml}"

echo "==> Installing Docker, Compose, NVIDIA runtime"
sudo apt-get update -y
sudo apt-get install -y docker.io docker-compose-plugin nvidia-container-toolkit
sudo usermod -aG docker "$USER" || true
sudo systemctl restart docker

echo "==> Using base compose: $BASE_COMPOSE"
echo "==> Using override:     $OVERRIDE_YML"

if [ ! -f "$BASE_COMPOSE" ]; then
  echo "Base compose not found: $BASE_COMPOSE"
  exit 1
fi
if [ ! -f "$OVERRIDE_YML" ]; then
  echo "Override not found: $OVERRIDE_YML"
  exit 1
fi

cd "$(dirname "$BASE_COMPOSE")"

echo "==> Bringing up Jarvis with Jetson overrides"
docker compose \
  -f "$BASE_COMPOSE" \
  -f "$OVERRIDE_YML" \
  up -d --build

echo "==> Logs (last 50)"
docker compose logs -n 50 jarvis || true
