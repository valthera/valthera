#!/usr/bin/env bash
set -euo pipefail

# Auto-detect repo directory if not set
if [ -z "${REPO_DIR:-}" ]; then
    # Try to find the repo root by looking for devices/jarvis directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -d "$SCRIPT_DIR/../../devices/jarvis" ]; then
        REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
    else
        REPO_DIR="/opt/valthera/valthera"
    fi
fi
BASE_COMPOSE="${BASE_COMPOSE:-$REPO_DIR/devices/jarvis/docker-compose.yml}"
OVERRIDE_YML="${OVERRIDE_YML:-$REPO_DIR/devices/jarvis/jetson.jarvis.override.yml}"

echo "==> Installing Docker, Compose, NVIDIA runtime"
sudo apt-get update -y

# Check if Docker is already installed
if ! command -v docker &> /dev/null; then
    echo "==> Installing Docker..."
    sudo apt-get install -y docker.io docker-compose-plugin
else
    echo "==> Docker already installed, skipping Docker installation"
fi

# Install NVIDIA container toolkit
sudo apt-get install -y nvidia-container-toolkit

# Add user to docker group and restart docker
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

echo "==> Bringing up Jarvis services with Jetson overrides"
docker compose \
  -f "$BASE_COMPOSE" \
  -f "$OVERRIDE_YML" \
  up -d --build

echo "==> Waiting for services to be ready..."
sleep 10

echo "==> Checking service health..."
echo "API Service:"
docker compose logs -n 20 jarvis-api || true

echo ""
echo "Web Service:"
docker compose logs -n 20 jarvis-web || true

echo ""
echo "==> Service Status:"
docker compose ps

echo ""
echo "==> Access URLs:"
echo "Web Interface: http://jarvis.local:3000"
echo "API Health:   http://jarvis.local:8001/health"
echo "API Docs:     http://jarvis.local:8001/docs"