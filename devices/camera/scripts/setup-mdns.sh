#!/usr/bin/env bash
set -euo pipefail

HOSTNAME_ARG="${1:-jetson}"
SERVICE_NAME="${2:-Valthera Camera}"
PORT="${3:-8000}"

echo "==> Setting hostname to ${HOSTNAME_ARG}"
sudo hostnamectl set-hostname "${HOSTNAME_ARG}"

echo "==> Installing Avahi (mDNS)"
sudo apt-get update -y
sudo apt-get install -y avahi-daemon avahi-utils
sudo systemctl enable --now avahi-daemon

echo "==> Advertising _http._tcp on port ${PORT} as '${SERVICE_NAME}'"
sudo mkdir -p /etc/avahi/services
sudo tee /etc/avahi/services/valthera-camera.service >/dev/null <<XML
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">${SERVICE_NAME}</name>
  <service>
    <type>_http._tcp</type>
    <port>${PORT}</port>
    <txt-record>path=/</txt-record>
  </service>
  <service>
    <type>_valthera-camera._tcp</type>
    <port>${PORT}</port>
  </service>
  
</service-group>
XML

sudo systemctl restart avahi-daemon

if command -v ufw >/dev/null 2>&1; then
  sudo ufw allow 5353/udp || true
  sudo ufw allow ${PORT}/tcp || true
fi

echo "==> Done. Reachable via http://${HOSTNAME_ARG}.local:${PORT}"

